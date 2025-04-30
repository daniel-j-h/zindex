#!/usr/bin/env python3

import sys
import argparse
from pathlib import Path

# todo: add proper dependency management
# pip install duckdb

import duckdb


def main(args):
    # Below is an example query but what we really need to do is
    # take a query bounding box of [lngmin, latmin, lngmax, latmax]
    # and turn that into [zmin, zmax] and then prune it with the
    # LITMAX/BIGMIN optimization technique. Then below we can
    # query by multiple z ranges. It's not obvious to me if it's
    # beneficial to prune down to the exact z ranges or if there
    # is a trade off where we prune to rough z ranges and add an
    # additional predicate on the bounding box as in
    #
    #   WHERE (z BETWEEN lo AND hi
    #          AND lng BETWEEN lngmin AND lngmax
    #          AND lat BETWEEN latmin AND latmax)
    #
    # to reduce the number of queries we need to make in total.
    #
    # This is similar to the optimization in zbush to only compute
    # BIGMIN and jump to it if the range of irrelevant data is large:
    #
    # https://github.com/daniel-j-h/zbush/blob/1bed328cc2788cd516d3fca7b0a546f6c27d9983/index.js#L144-L171

    points = duckdb.execute("""
        select lng, lat from 'berlin-latest-hydrants.parquet' where
          z between 3973762480109379858 and 3973762480196724606
        """).fetchall()

    for lng, lat in points:
        lng = round(lng / 10000000 - 180, 6)
        lat = round(lat / 10000000 - 90, 6)

        print(f"point: {lng}, {lat}", file=sys.stderr)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("input", type=Path, help=".parquet")

    main(parser.parse_args())
