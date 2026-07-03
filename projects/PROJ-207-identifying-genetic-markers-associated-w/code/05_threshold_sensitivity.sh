#!/bin/bash
# Wrapper script to execute threshold sensitivity analysis
# This script runs the Python implementation of T021.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

INPUT_FILE="${PROJECT_ROOT}/data/interim/gwas_raw.tsv"
OUTPUT_FILE="${PROJECT_ROOT}/data/processed/threshold_sensitivity_report.tsv"

# Check if input file exists
if [ ! -f "$INPUT_FILE" ]; then
    echo "Error: Input file not found: $INPUT_FILE"
    echo "Please ensure the GWAS pipeline (T017) has been run successfully."
    exit 1
fi

echo "Running threshold sensitivity analysis..."
echo "Input: $INPUT_FILE"
echo "Output: $OUTPUT_FILE"

python3 "${PROJECT_ROOT}/code/utils/threshold_sensitivity.py" \
    --input "$INPUT_FILE" \
    --output "$OUTPUT_FILE"

if [ $? -eq 0 ]; then
    echo "Threshold sensitivity analysis completed successfully."
    echo "Report saved to: $OUTPUT_FILE"
else
    echo "Threshold sensitivity analysis failed."
    exit 1
fi