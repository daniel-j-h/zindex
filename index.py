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

        self.lngs = []
        self.lats = []

    def node(self, n):
        # https://wiki.openstreetmap.org/wiki/Tag:emergency%3Dfire_hydrant

        if "emergency" not in n.tags or n.tags["emergency"] != "fire_hydrant":
            return

        self.lngs.append(n.location.lon)
        self.lats.append(n.location.lat)


def main(args):
    handler = PointHandler()
    handler.apply_file(args.input)

    zs = []
    lngs = []
    lats = []

    for lng, lat in zip(handler.lngs, handler.lats):
        # 32-bit Z value for a 16-bit x,y-grid
        lng16 = int((lng + 180) * ((2**16 - 1) / 360))
        lat16 = int((lat +  90) * ((2**16 - 1) / 180))
        assert 0 <= lng16 <= 2**16-1
        assert 0 <= lat16 <= 2**16-1

        z32 = pyzorder.pymorton.interleave(lng16, lat16)
        assert 0 <= z32 <= 2**32-1

        zs.append(z32)

        # 32-bit unsigned fixed representation
        lng32 = int((lng + 180) * 10000000)
        lat32 = int((lat +  90) * 10000000)
        assert 0 <= lng32 <= 2**32-1
        assert 0 <= lat32 <= 2**32-1

        lngs.append(lng32)
        lats.append(lat32)

    schema = pyarrow.schema([
        pyarrow.field("z", pyarrow.uint32(), nullable=False),
        pyarrow.field("lng", pyarrow.uint32(), nullable=False),
        pyarrow.field("lat", pyarrow.uint32(), nullable=False),
    ])

    table = pyarrow.Table.from_arrays([zs, lngs, lats], schema=schema)
    table = table.sort_by("z")

    # Open question: Do we need to fine-tune the row group
    # size and/or the page size below for our use case some
    # more? We want to support rather local bounding box
    # queries translating into a few linear range queries.
    #
    # Open question: What about column encoding, compression

    pyarrow.parquet.write_table(table, args.out,
        sorting_columns=[pyarrow.parquet.SortingColumn(0)],
        data_page_size=2**16, row_group_size=2**20)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("input", type=Path, help=".osm.pbf")
    parser.add_argument("-o", "--out", type=Path, required=True, help="path to output parquet file")

    main(parser.parse_args())
