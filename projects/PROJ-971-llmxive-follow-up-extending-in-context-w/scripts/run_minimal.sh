#!/usr/bin/env bash
set -euo pipefail

# Run the minimal end‑to‑end pipeline on 50 clips.
# The run_end_to_end module generates the clips, extracts descriptors,
# and prints a summary table.
python -m src.pipeline.run_end_to_end --subset 50
