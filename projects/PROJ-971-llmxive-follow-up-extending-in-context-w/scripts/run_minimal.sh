#!/usr/bin/env bash
set -euo pipefail

# ----------------------------------------------------------------------
# Minimal pipeline runner
#
# 1. Generate a reproducible set of interaction clips (default 50).
# 2. Extract latent statistical descriptors for *all* clips and write the
#    full descriptor CSV to ``data/processed/descriptors.csv``.
# 3. Copy the full CSV to the legacy shortcut location
#    ``data/descriptors_subset.csv`` (used by older documentation).
# ----------------------------------------------------------------------

# Run the end‑to‑end driver which creates the subset descriptor CSV.
python -m src.pipeline.run_end_to_end --subset 50

# Resolve the paths using the project's toolkit helpers.
src_path=$(python - <<PY
from llmxive_toolkit import paths
print(paths.data('descriptors_subset.csv'))
PY
)
dst_path=$(python - <<PY
from llmxive_toolkit import paths
print(paths.data('processed', 'descriptors.csv'))
PY
)

# Copy the subset file to the full‑descriptor location.
cp "$src_path" "$dst_path"

echo "Descriptors written to $dst_path (full) and $src_path (subset)."
