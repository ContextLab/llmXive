#!/usr/bin/env bash
# Run the minimal end-to-end Auto-ICWM pipeline on 50 clips.
set -e
python -m src.pipeline.run_end_to_end --subset 50
test -f data/descriptors_subset.csv
echo "run_minimal: data/descriptors_subset.csv present"