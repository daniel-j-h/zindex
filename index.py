#!/usr/bin/env python3

import sys
import argparse
from pathlib import Path

# todo: add proper dependency management
# pip install osmium pyarrow pyzorder

import osmium

import pyarrow
import pyarrow.parquet

import pyzorder


class PointHandler(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()

        self.lng = []
        self.lat = []

    def node(self, n):
        # https://wiki.openstreetmap.org/wiki/Tag:emergency%3Dfire_hydrant

        if "emergency" not in n.tags or n.tags["emergency"] != "fire_hydrant":
            return

        self.lng.append(int((n.location.lon + 180) * 10000000))
        self.lat.append(int((n.location.lat +  90) * 10000000))


def main(args):
    handler = PointHandler()
    handler.apply_file(args.input)

    z = [pyzorder.pymorton.interleave(lng, lat)
         for lng, lat in zip(handler.lng, handler.lat)]

    # Open question: Should the Z value be of type u64 as in
    # we interleave the two u32 fixed point lng, lat values
    # or would a u32 Z value be good enough which translates
    # to a coarse grid of lng, lat we can query by?

    schema = pyarrow.schema([
        pyarrow.field("z", pyarrow.uint64(), nullable=False),
        pyarrow.field("lng", pyarrow.uint32(), nullable=False),
        pyarrow.field("lat", pyarrow.uint32(), nullable=False),
    ])

    table = pyarrow.Table.from_arrays([z, handler.lng, handler.lat], schema=schema)
    table.sort_by("z")

    # Open Question: Do we need multiple files for partitioning
    # by a Z value prefix or is a single file with many row groups
    # good enough? Related: How big should the row groups then be?
    # What I found in the docs is that the WHERE predicate will get
    # pushed down in the query to skip over row groups but we also
    # don't want too many row groups because they're coming with
    # their own overhead. We need to explore here or ask folks
    # who understand parquet and duckdb a bit better than me
    # spending two hours in my evening on this.

    pyarrow.parquet.write_table(table, args.out,
        sorting_columns=[pyarrow.parquet.SortingColumn(0)],
        row_group_size=2**12)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("input", type=Path, help=".osm.pbf")
    parser.add_argument("-o", "--out", type=Path, required=True, help="path to output parquet file")

    main(parser.parse_args())
