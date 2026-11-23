#!/usr/bin/env bash
set -e
# Run the citation‑gate validation script.
python "$(dirname "$0")/../tools/reference_validator.py" --threshold 0.8
# If the script exits with 0, the marker file will have been created.
echo "Citation‑gate validation completed successfully."