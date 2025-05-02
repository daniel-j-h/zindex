#!/usr/bin/env python3

import sys
import argparse
from pathlib import Path

# todo: add proper dependency management
# pip install duckdb pyzorder

import duckdb

import pyzorder


def main(args):
    # See index.py: Z values are 32-bit on a 16-bit x,y-grid
    # in the parquet column. The full 32-bit lng, lat are
    # available in the lng, lat columns to use.

    xmin16 = int((args.lngmin + 180) * ((2**16 - 1) / 360))
    xmax16 = int((args.lngmax + 180) * ((2**16 - 1) / 360))
    assert 0 <= xmin16 <= 2**16-1
    assert 0 <= xmax16 <= 2**16-1

    ymin16 = int((args.latmin +  90) * ((2**16 - 1) / 180))
    ymax16 = int((args.latmax +  90) * ((2**16 - 1) / 180))
    assert 0 <= ymin16 <= 2**16-1
    assert 0 <= ymax16 <= 2**16-1

    assert xmin16 <= xmax16
    assert ymin16 <= ymax16

    zmin32 = pyzorder.pymorton.interleave(xmin16, ymin16)
    zmax32 = pyzorder.pymorton.interleave(xmax16, ymax16)
    assert 0 <= zmin32 <= 2**32-1
    assert 0 <= zmax32 <= 2**32-1

    assert zmin32 <= zmax32

    # We now have a range of [zmin, zmax] we know all our
    # points are within. We can now prune this range by
    # irrelevant data ranges due to Z discontinuities
    # using the BIGMIN optimization implemented in the
    # pyzorder packages as next_zorder_index(z) below.

    zindex = pyzorder.ZOrderIndexer((xmin16, xmax16), (ymin16, ymax16))

    zs = []

    while zmin32 < zmax32:
        zs.append(zmin32)
        zmin32 = zindex.next_zorder_index(zmin32)

    zs.append(zmax32)

    # The list zs now contains all Z values pruned by
    # irrelevant data ranges, meaning our points are
    # exactly in there. We now have multiple options:
    #
    # 1. Do a single SQL query with a WHERE IN operator
    #    and list all values in zs. Pro: Single query
    #    Con: Will most likely cause troubles when
    #    the list of Z values gets big.
    #
    # 2. Split the list into sub-ranges and make multiple
    #    SQL queries with WHERE z BETWEEN lo and hi. Pro:
    #    We can run multiple queries potentially in parallel.
    #    Con: It might create many small queries when points
    #    are sparse and the query window is large.
    #    Example for three sub-queries querying ranges on z:
    #    [1001, 1003], [1007, 1009], [4095, 4096]
    #
    # 3. Split the list into sub-ranges and make multiple
    #    SQL queries with WHERE z BETWEEN lo and hi but
    #    allow the sub-ranges to be non-contiguous and
    #    add in the WHERE filter in addition
    #      AND lng BETWEEN lngmin AND lngmax
    #      AND lat BETWEEN latmin AND latmax
    #    Pro: This allows the query engine to make use of
    #    the sorting on z to pre-filter very efficiently
    #    and then filter the candidate points by lng, lat
    #    exactly. It's the best solution of the three
    #    allowing us to tune how many sub-queries to run
    #    vs. how much exact filtering the query engine
    #    will have to do. Same example from above,
    #    but allowing non-contiguous ranges:
    #    [1001, 1009], [4095, 4096]. Note how the ranges
    #    [1001, 1003] and [1007, 1009] get merged into one
    #    and the precise filtering by lng, lat will take
    #    care of the rest.
    #
    # All three approaches are very efficient since they
    # always filter by the z column (WHERE z ...) which
    # benefits from the z sorting in addition to the row
    # group and data page information in the parquet file.

    lngmin32 = int((args.lngmin + 180) * ((2**32 - 1) / 360))
    lngmax32 = int((args.lngmax + 180) * ((2**32 - 1) / 360))
    latmin32 = int((args.latmin +  90) * ((2**32 - 1) / 180))
    latmax32 = int((args.latmax +  90) * ((2**32 - 1) / 180))

    assert 0 <= lngmin32 <= 2**32-1
    assert 0 <= lngmax32 <= 2**32-1
    assert 0 <= latmin32 <= 2**32-1
    assert 0 <= latmax32 <= 2**32-1

    assert lngmin32 <= lngmax32
    assert latmin32 <= latmax32

    points = duckdb.execute(f"""
        select
          lng, lat
        from
          'berlin-latest-hydrants.parquet'
        where
          z in ({','.join(map(str, zs))})
          and lng between {lngmin32} and {lngmax32}
          and lat between {latmin32} and {latmax32};
        """).fetchall()

    for lng32, lat32 in points:
        assert lngmin32 <= lng32 <= lngmax32
        assert latmin32 <= lat32 <= latmax32

        lng = round(lng32 / ((2**32 - 1) / 360) - 180, 6)
        lat = round(lat32 / ((2**32 - 1) / 180) -  90, 6)

        print(f"point: {lng}, {lat}", file=sys.stderr)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("--lngmin", type=float, default=13.4083)
    parser.add_argument("--latmin", type=float, default=52.5217)
    parser.add_argument("--lngmax", type=float, default=13.4115)
    parser.add_argument("--latmax", type=float, default=52.5234)

    main(parser.parse_args())
