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
    table = table.sort_by("z")

    # Open question: Do we need to fine-tune the row group
    # size and/or the page size below for our use case some
    # more? We want to support rather local bounding box
    # queries translating into a few linear range queries.

    pyarrow.parquet.write_table(table, args.out,
        sorting_columns=[pyarrow.parquet.SortingColumn(0)],
        data_page_size=2**16, row_group_size=2**20)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("input", type=Path, help=".osm.pbf")
    parser.add_argument("-o", "--out", type=Path, required=True, help="path to output parquet file")

    main(parser.parse_args())
