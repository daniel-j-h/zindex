SHELL = /bin/sh
MAKEFLAGS += --no-builtin-rules

.SUFFIXES:
.DELETE_ON_ERROR:
.FEATURES: output-sync


.PHONY: osm
osm:
	@curl --proto '=https' --tlsv1.3 -sSfO https://download.geofabrik.de/europe/germany/berlin-latest.osm.pbf


.PHONY: clean
clean:
	@rm -f *.osm.pbf *.parquet
