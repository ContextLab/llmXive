#!/usr/bin/env bash
set -euo pipefail

# Activate virtualenv and set PYTHONPATH via quickstart.sh
source "$(dirname "$0")/quickstart.sh"

echo "Running Step 1: Minimal end-to-end pipeline..."
# This generates clips, extracts descriptors to data/processed/descriptors.csv,
# and creates the legacy shortcut data/descriptors_subset.csv.
python -m src.pipeline.run_end_to_end --subset 50

echo "Running Step 2: Task complexity computation..."
# This uses data/processed/descriptors.csv and writes data/processed/task_complexity.csv.
python -m src.pipeline.compute_complexity

echo "Minimal pipeline completed successfully."
