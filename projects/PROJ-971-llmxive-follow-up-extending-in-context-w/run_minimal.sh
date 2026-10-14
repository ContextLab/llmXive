#!/usr/bin/env bash
# Minimal end-to-end Auto-ICWM pipeline: 50 clips -> descriptors CSV.
# Runs the real pipeline (clip generation + latent descriptor extraction)
# and writes data/descriptors_subset.csv.
set -e
cd "$(dirname "$0")"
if [ -f .venv/bin/activate ]; then
    # shellcheck disable=SC1091
    source .venv/bin/activate
fi
export PYTHONPATH="${PWD}:${PYTHONPATH:-}"
export PYTHONHASHSEED=0
python -m src.pipeline.run_end_to_end --subset 50
# Verify the declared output exists and is non-empty.
test -s data/descriptors_subset.csv
echo "OK: data/descriptors_subset.csv exists ($(wc -l < data/descriptors_subset.csv) lines)"
