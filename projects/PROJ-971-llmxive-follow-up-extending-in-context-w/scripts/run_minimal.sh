#!/usr/bin/env bash
set -euo pipefail

# Run the minimal end‑to‑end Auto‑ICWM pipeline.
# This will:
#   1. Generate 50 reproducible CartPole interaction clips in data/raw/
#   2. Extract statistical descriptors and write data/processed/descriptors.csv
#   3. Create the legacy shortcut CSV data/descriptors_subset.csv
# The script exits with status 0 on success.
python -m src.pipeline.run_end_to_end --subset 50
