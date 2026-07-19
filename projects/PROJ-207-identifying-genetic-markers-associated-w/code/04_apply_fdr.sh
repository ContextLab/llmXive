#!/bin/bash
# T022: Apply Benjamini-Hochberg FDR Correction to GWAS Results
#
# This script post-processes the raw GWAS output from T017 (PLINK)
# by applying the Benjamini-Hochberg procedure to control the False
# Discovery Rate (FDR).
#
# Input:  data/interim/gwas_raw.tsv (produced by code/03_gwas.sh / T017)
# Output: data/processed/gwas_results_fdr.tsv (FR-004, FR-005)
#
# Dependencies:
#   - code/utils/fdr_correction.py (T020)
#   - data/interim/gwas_raw.tsv (must exist from T017)

set -e

# Define paths relative to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

INPUT_FILE="${PROJECT_ROOT}/data/interim/gwas_raw.tsv"
OUTPUT_FILE="${PROJECT_ROOT}/data/processed/gwas_results_fdr.tsv"
FDR_SCRIPT="${PROJECT_ROOT}/code/utils/fdr_correction.py"

echo "=== T022: Applying FDR Correction ==="

# Check input file exists
if [ ! -f "$INPUT_FILE" ]; then
    echo "ERROR: Input file not found: $INPUT_FILE" >&2
    echo "This file should be produced by code/03_gwas.sh (T017)." >&2
    exit 1
fi

# Check FDR script exists
if [ ! -f "$FDR_SCRIPT" ]; then
    echo "ERROR: FDR correction script not found: $FDR_SCRIPT" >&2
    exit 1
fi

# Ensure output directory exists
OUTPUT_DIR="$(dirname "$OUTPUT_FILE")"
mkdir -p "$OUTPUT_DIR"

echo "Input:  $INPUT_FILE"
echo "Output: $OUTPUT_FILE"

# Execute FDR correction
# The Python script handles reading TSV, applying BH correction,
# and writing the output TSV with q_values.
python "$FDR_SCRIPT" \
    --input "$INPUT_FILE" \
    --output "$OUTPUT_FILE"

# Verify output was created
if [ -f "$OUTPUT_FILE" ]; then
    echo "SUCCESS: FDR correction complete. Output written to $OUTPUT_FILE"
    # Optional: print a quick summary if the file is not empty
    if [ -s "$OUTPUT_FILE" ]; then
        LINE_COUNT=$(wc -l < "$OUTPUT_FILE")
        echo "Output contains $LINE_COUNT lines (including header)."
    fi
else
    echo "ERROR: Output file was not created: $OUTPUT_FILE" >&2
    exit 1
fi

echo "=== T022 Complete ==="
