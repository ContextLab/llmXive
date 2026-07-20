#!/bin/bash
# T022: Apply Benjamini-Hochberg FDR correction to GWAS results
#
# This script post-processes the raw GWAS output (data/interim/gwas_raw.tsv)
# using the Benjamini-Hochberg procedure implemented in code/utils/fdr_correction.py.
# It writes the final results to data/processed/gwas_results_fdr.tsv.
#
# Dependencies:
#   - code/utils/fdr_correction.py (T020)
#   - data/interim/gwas_raw.tsv (Output of T017/code/03_gwas.sh)
#
# Exit Codes:
#   0: Success
#   1: Input file not found or processing error
#   2: Missing dependencies

set -e

# Define paths relative to project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

INPUT_FILE="$PROJECT_ROOT/data/interim/gwas_raw.tsv"
OUTPUT_FILE="$PROJECT_ROOT/data/processed/gwas_results_fdr.tsv"
FDR_SCRIPT="$PROJECT_ROOT/code/utils/fdr_correction.py"

echo "=== T022: Applying FDR Correction ==="

# Check if input file exists
if [ ! -f "$INPUT_FILE" ]; then
    echo "ERROR: Input file not found: $INPUT_FILE"
    echo "Please ensure T017 (GWAS execution) has completed successfully."
    exit 1
fi

# Check if FDR script exists
if [ ! -f "$FDR_SCRIPT" ]; then
    echo "ERROR: FDR correction script not found: $FDR_SCRIPT"
    exit 1
fi

# Ensure output directory exists
mkdir -p "$(dirname "$OUTPUT_FILE")"

# Execute FDR correction
echo "Processing: $INPUT_FILE"
echo "Output: $OUTPUT_FILE"

python "$FDR_SCRIPT" \
    --input "$INPUT_FILE" \
    --output "$OUTPUT_FILE"

if [ $? -eq 0 ]; then
    echo "=== T022 Complete ==="
    echo "FDR-corrected results written to: $OUTPUT_FILE"
    exit 0
else
    echo "ERROR: FDR correction failed."
    exit 1
fi