#!/bin/bash
# T022: Apply Benjamini-Hochberg FDR correction to GWAS results
# Input: data/interim/gwas_raw.tsv (produced by T017)
# Output: data/processed/gwas_results_fdr.tsv
# Dependencies: code/utils/fdr_correction.py (T020)

set -e

INPUT_FILE="data/interim/gwas_raw.tsv"
OUTPUT_FILE="data/processed/gwas_results_fdr.tsv"

echo "Starting FDR correction pipeline step..."

# Verify input file exists
if [ ! -f "$INPUT_FILE" ]; then
    echo "Error: Input file not found: $INPUT_FILE"
    echo "Ensure T017 (code/03_gwas.sh) has been executed successfully."
    exit 1
fi

# Ensure output directory exists
mkdir -p "$(dirname "$OUTPUT_FILE")"

echo "Applying Benjamini-Hochberg FDR correction..."
echo "Input:  $INPUT_FILE"
echo "Output: $OUTPUT_FILE"

# Execute the Python FDR correction utility
python code/utils/fdr_correction.py \
    --input "$INPUT_FILE" \
    --output "$OUTPUT_FILE"

if [ $? -eq 0 ] && [ -f "$OUTPUT_FILE" ]; then
    echo "SUCCESS: FDR correction complete."
    echo "Results written to: $OUTPUT_FILE"
    echo "Significant SNPs (q < 0.05) flagged in 'significant' column."
else
    echo "Error: FDR correction failed or output file not created."
    exit 1
fi