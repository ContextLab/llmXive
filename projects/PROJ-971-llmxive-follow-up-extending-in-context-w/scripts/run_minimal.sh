#!/usr/bin/env bash
set -euo pipefail

# ----------------------------------------------------------------------
# Minimal end‑to‑end pipeline used by the Quickstart.
# 1. Generate a deterministic set of 50 interaction clips.
# 2. Extract the three latent descriptors for each clip.
# 3. Copy the resulting CSV to the top‑level location expected by the
#    Quickstart documentation (data/descriptors_subset.csv).
# ----------------------------------------------------------------------

# Generate clips (defaults to 50 clips)
python -m src.pipeline.generate_clips

# Extract descriptors; defaults read from data/raw and write to
# data/processed/descriptors.csv
python -m src.pipeline.extract_descriptors

# Copy the processed file to the shortcut location used by the Quickstart.
PROCESSED_CSV=$(python -c "from llmxive_toolkit import paths; print(paths.data('processed','descriptors.csv'))")
SUBSET_CSV=$(python -c "from llmxive_toolkit import paths; print(paths.data('descriptors_subset.csv'))")
cp "$PROCESSED_CSV" "$SUBSET_CSV"

echo "Minimal pipeline completed. Descriptor CSV available at $SUBSET_CSV"