#!/usr/bin/env bash
#
# run_minimal.sh – execute the minimal end‑to‑end pipeline on 50 clips.
#
set -e

# Run the driver module; it will generate clips, extract descriptors,
# and print a full table of 50 rows.
python -m src.pipeline.run_end_to_end --subset 50