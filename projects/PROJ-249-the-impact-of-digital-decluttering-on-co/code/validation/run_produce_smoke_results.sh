#!/usr/bin/env bash
set -e
python -m code.validation.produce_smoke_results
# Verify that the output file exists and is non‑empty
OUTPUT=$(python - <<PY
from llmxive_toolkit import paths
print(paths.data("results", "smoke_results.json"))
PY
)
if [[ ! -s "$OUTPUT" ]]; then
  echo "Smoke results file is empty or missing."
  exit 1
fi
echo "Smoke results generated successfully at $OUTPUT"