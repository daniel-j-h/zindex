# ZIndex

Proof of concept for a static spatial point index realized with Parquet and Z-Curve + BIGMIN querying.

- See the `index.py` file for creating the .parquet file from an .osm.pbf file
- See the `query.py` file as an example for querying the .parquet file

## Testing

I have generated the file `berlin-latest-hydrants.parquet` and have a GitHub Page serve it.

This means we can make queries against it with DuckDB for testing purpose like so:

```sql
select z, lng, lat
from 'https://daniel-j-h.github.io/zindex/berlin-latest-hydrants.parquet'
limit 5;
```

```
┌─────────────────────┬────────────┬────────────┐
│          z          │    lng     │    lat     │
│       uint64        │   uint32   │   uint32   │
├─────────────────────┼────────────┼────────────┤
│ 3973785672514116087 │ 1934751583 │ 1424080557 │
│ 3973784600528416127 │ 1933609407 │ 1424172775 │
│ 3973780144626905536 │ 1935588952 │ 1423883976 │
│ 3973785082335509236 │ 1934421070 │ 1424446460 │
│ 3973773851562393572 │ 1932084858 │ 1425122044 │
└─────────────────────┴────────────┴────────────┘
```


## License

Copyright © 2025 Daniel J. H.

Distributed under the MIT License (MIT).
