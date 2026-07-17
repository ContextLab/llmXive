#!/bin/bash
# T022: Apply FDR Correction to GWAS Results
#
# This script post-processes the raw GWAS output using the Benjamini-Hochberg
# method implemented in code/utils/fdr_correction.py.
#
# Input: data/interim/gwas_raw.tsv (produced by T017/code/03_gwas.sh)
# Output: data/processed/gwas_results_fdr.tsv
#
# Dependency: code/utils/fdr_correction.py (T020)

set -e

INPUT_FILE="data/interim/gwas_raw.tsv"
OUTPUT_FILE="data/processed/gwas_results_fdr.tsv"

# Verify input file exists
if [ ! -f "$INPUT_FILE" ]; then
    echo "ERROR: Input file not found: $INPUT_FILE"
    echo "Please ensure T017 (code/03_gwas.sh) has been executed successfully."
    exit 1
fi

# Ensure output directory exists
mkdir -p "$(dirname "$OUTPUT_FILE")"

echo "Applying Benjamini-Hochberg FDR correction..."
echo "Input:  $INPUT_FILE"
echo "Output: $OUTPUT_FILE"

# Execute the FDR correction utility
# The script handles reading the TSV, calculating q-values, and writing the output
# with the mandatory disclaimer.
python code/utils/fdr_correction.py \
    --input "$INPUT_FILE" \
    --output "$OUTPUT_FILE"

# Verify output was created
if [ ! -f "$OUTPUT_FILE" ]; then
    echo "ERROR: Output file was not created: $OUTPUT_FILE"
    exit 1
fi

echo "FDR correction complete. Results written to $OUTPUT_FILE"

# Display a summary of significant SNPs
SIGNIFICANT_COUNT=$(tail -n +3 "$OUTPUT_FILE" | awk -F'\t' '$NF == "True"' | wc -l)
TOTAL_COUNT=$(tail -n +3 "$OUTPUT_FILE" | wc -l)

echo "Summary:"
echo "  Total SNPs analyzed: $TOTAL_COUNT"
echo "  Significant (q < 0.05): $SIGNIFICANT_COUNT"