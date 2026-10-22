#!/usr/bin/env bash
# scripts/run_minimal.sh
#
# Minimal training‑set pipeline for task T021.
# Generates 200 training interaction clips, extracts latent descriptors,
# and computes the independent task‑complexity metric.
#
# The script is idempotent: running it again will overwrite existing
# files with the same deterministic content.
#
# Expected outputs:
#   data/processed/descriptors.csv        – descriptor table for 200 clips
#   data/processed/task_complexity.csv   – sub‑goal count per clip
#   reports/complexity_summary.txt       – Pearson correlation log
#
# Failure of any step aborts the script (set -e). All required
# environment activation is performed via quickstart.sh.

set -euo pipefail

# Activate the virtual environment (if present) and set PYTHONPATH.
# This mirrors the behaviour of the project's quickstart.
source "$(dirname "${BASH_SOURCE[0]}")/quickstart.sh"

echo "=== T021: Generating 200 training clips ==="
python -m src.pipeline.generate_training_clips

echo "=== T021: Extracting latent descriptors ==="
python -m src.pipeline.extract_descriptors

echo "=== T021: Computing task‑complexity metric ==="
python -m src.pipeline.compute_complexity

echo "=== T021 completed: descriptors and task_complexity generated ==="