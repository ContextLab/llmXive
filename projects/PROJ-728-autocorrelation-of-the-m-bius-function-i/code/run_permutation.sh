#!/usr/bin/env bash
set -e
# Ensure the required directories exist
mkdir -p data/processed
# Run the permutation driver in pipeline mode, creating the
# statistics CSV required by downstream stages.
python -m code.permutation \
    --stats data/processed/autocorrelation_stats.csv \
    --array data/raw/mobius_array.npy