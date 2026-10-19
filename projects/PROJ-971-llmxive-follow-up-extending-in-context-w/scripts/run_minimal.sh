#!/usr/bin/env bash
set -euo pipefail

# Activate virtualenv / set PYTHONPATH
source "$(dirname "$0")/quickstart.sh"

# Step 1: Run the minimal end‑to‑end pipeline (generates clips,
#         extracts descriptors, and writes the subset CSV).
python -m src.pipeline.run_end_to_end --subset 50

# Step 2: Compute the independent task‑complexity metric and the
#         Pearson correlation with latent variance.
python code/src/pipeline/compute_complexity.py
