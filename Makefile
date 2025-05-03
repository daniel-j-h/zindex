SHELL = /bin/sh
MAKEFLAGS += --no-builtin-rules

.SUFFIXES:
.DELETE_ON_ERROR:
.FEATURES: output-sync


all:
	@echo osm
	@echo index
	@echo query
	@echo sh
	@echo help
	@echo clean

.PHONY: osm
osm:
	curl --proto '=https' --tlsv1.3 -sSfO https://download.geofabrik.de/europe/germany/berlin-latest.osm.pbf

.PHONY: index
index:
	python3 index.py berlin-latest.osm.pbf -o berlin-latest-hydrants.parquet

.PHONY: query
query:
	python3 query.py #berlin-latest-hydrants.parquet

.PHONY: sh
sh:
	@docker run -it -v $(CURDIR):/data:z -w /data debian:bookworm-slim bash

.PHONY: help
help:
	@echo
	@python3 index.py --help
	@echo
	@echo
	@python3 query.py --help
	@echo

.PHONY: clean
clean:
	@rm -f *.osm.pbf *.parquet
