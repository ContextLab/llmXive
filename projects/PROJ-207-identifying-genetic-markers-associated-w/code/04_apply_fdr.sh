#!/bin/bash
# T022: Apply FDR Correction to GWAS Results
# This script post-processes the raw GWAS output using the Benjamini-Hochberg
# procedure implemented in code/utils/fdr_correction.py.
#
# Input:  data/interim/gwas_raw.tsv (produced by T017/code/03_gwas.py)
# Output: data/processed/gwas_results_fdr.tsv
#
# Dependencies:
#   - code/utils/fdr_correction.py (T020)
#   - data/interim/gwas_raw.tsv (T017)

set -e

# Define paths relative to project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

INPUT_FILE="$PROJECT_ROOT/data/interim/gwas_raw.tsv"
OUTPUT_FILE="$PROJECT_ROOT/data/processed/gwas_results_fdr.tsv"
FDR_SCRIPT="$PROJECT_ROOT/code/utils/fdr_correction.py"

echo "=== T022: Applying FDR Correction ==="
echo "Input:  $INPUT_FILE"
echo "Output: $OUTPUT_FILE"

# Check if input file exists
if [ ! -f "$INPUT_FILE" ]; then
    echo "ERROR: Input file not found: $INPUT_FILE"
    echo "Please ensure T017 (GWAS execution) has completed successfully."
    exit 1
fi

# Check if FDR script exists
if [ ! -f "$FDR_SCRIPT" ]; then
    echo "ERROR: FDR correction script not found: $FDR_SCRIPT"
    echo "Please ensure T020 has been implemented."
    exit 1
fi

# Ensure output directory exists
mkdir -p "$(dirname "$OUTPUT_FILE")"

# Execute FDR correction
# The Python script handles the BH calculation and writes the final TSV
python "$FDR_SCRIPT" \
    --input "$INPUT_FILE" \
    --output "$OUTPUT_FILE"

# Verify output was created
if [ -f "$OUTPUT_FILE" ]; then
    echo "SUCCESS: FDR correction complete."
    echo "Output written to: $OUTPUT_FILE"
    echo "Preview (first 5 lines):"
    head -n 5 "$OUTPUT_FILE"
else
    echo "ERROR: Output file was not created."
    exit 1
fi