# ZIndex

Proof of concept for a very fast cloud-native static spatial index for 2D points based on a Z-Order space filling curve and BIGMIN search space pruning.

- See the `index.py` file for creating the .parquet file from an .osm.pbf file
- See the `query.py` file as an example for querying the .parquet file

Thanks to [Marco Neumann](https://github.com/crepererum) helping me understand Parquet.


## Usage

I have generated the file `berlin-latest-hydrants.parquet` and have a GitHub Page serve it

```bash
python3 index.py berlin-latest.osm.pbf -o berlin-latest-hydrants.parquet
```

This means we can make queries against it with DuckDB for testing purpose

```sql
select
  z, lng, lat
from
  'https://daniel-j-h.github.io/zindex/berlin-latest-hydrants.parquet'
limit 5;
```

```
┌────────────┬────────────┬────────────┐
│     z      │    lng     │    lat     │
│   uint32   │   uint32   │   uint32   │
├────────────┼────────────┼────────────┤
│ 3771284411 │ 1931291805 │ 1423846691 │
│ 3771284411 │ 1931292153 │ 1423846687 │
│ 3771284411 │ 1931307364 │ 1423846371 │
│ 3771284414 │ 1931320019 │ 1423846257 │
│ 3771296433 │ 1933943341 │ 1423750868 │
└────────────┴────────────┴────────────┘
```


## How It Works

We sort 2d points along a Z-order space-filling curve and use an optimization ("BIGMIN") to skip over irrelevant data when walking the curve.

| Z-curve with query bounding box | Z-curve with BIGMIN skipping |
|-|-|
| ![](./1.jpg) | ![](./2.jpg) |

If you are interested in a high-level overview check out [my blog post](https://www.openstreetmap.org/user/daniel-j-h/diary/406584) and see [zbush](https://github.com/daniel-j-h/zbush/).



## License

Copyright © 2025 Daniel J. H.

Distributed under the MIT License (MIT).
