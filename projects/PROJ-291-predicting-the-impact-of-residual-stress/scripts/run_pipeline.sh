#!/usr/bin/env bash
set -e

# 1. Verify the environment
bash scripts/env_check.sh

# 2. Ingest & preprocess (the ingest script now falls back to the bundled
#    raw CSVs when no external URLs are supplied)
python -m src.ingest.ingest --output data/processed/unified_fatigue.csv

# Additional pipeline stages (feature construction, training, etc.) are
# invoked by later tasks.  They are intentionally omitted here because
# they are not part of T001.
