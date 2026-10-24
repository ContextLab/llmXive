#!/usr/bin/env bash
set -e
# Ensure the reference validator runs and creates the marker file.
python "$(dirname "$0")/reference_validator.py" --threshold 0.8
# Verify marker file existence (optional sanity check)
if [ -f "$(python -c 'import os; from llmxive_toolkit import paths; print(paths.path("state","validation","citation_gate_passed.txt"))')" ]; then
  echo "Citation gate passed."
else
  echo "Citation gate failed: marker file not created."
  exit 1
fi
