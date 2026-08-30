#!/bin/bash
# T022: Merge PLINK raw results with FDR-corrected results
# Input: data/interim/gwas_raw.tsv (from T017), data/interim/gwas_fdr.tsv (from T020)
# Output: data/processed/gwas_results_fdr.tsv

set -e

RAW_FILE="data/interim/gwas_raw.tsv"
FDR_FILE="data/interim/gwas_fdr.tsv"
OUTPUT_FILE="data/processed/gwas_results_fdr.tsv"

# Ensure input files exist
if [ ! -f "$RAW_FILE" ]; then
    echo "Error: Raw GWAS file not found: $RAW_FILE"
    exit 1
fi

if [ ! -f "$FDR_FILE" ]; then
    echo "Error: FDR-corrected file not found: $FDR_FILE"
    exit 1
fi

# Ensure output directory exists
mkdir -p "$(dirname "$OUTPUT_FILE")"

# Merge logic:
# 1. Read raw file (columns: SNP, CHROM, POS, A1, A2, TEST, OBS_CT, BETA, SE, P, ODDS_RATIO)
# 2. Read FDR file (columns: rank, raw_p, q_value, significant)
# 3. Join on P (raw) = raw_p.
# 4. Sort final output by q_value ascending (most significant first).
# 5. Write to TSV.

python3 << 'PYTHON_SCRIPT'
import pandas as pd
import sys
import os

raw_path = "data/interim/gwas_raw.tsv"
fdr_path = "data/interim/gwas_fdr.tsv"
output_path = "data/processed/gwas_results_fdr.tsv"

try:
    # Load data
    # Raw file is expected to have a 'P' column (p-value)
    df_raw = pd.read_csv(raw_path, sep='\t')
    df_fdr = pd.read_csv(fdr_path, sep='\t')

    # Validate columns
    if 'P' not in df_raw.columns:
        raise ValueError(f"Raw file missing 'P' column. Columns found: {df_raw.columns.tolist()}")
    if 'raw_p' not in df_fdr.columns:
        raise ValueError(f"FDR file missing 'raw_p' column. Columns found: {df_fdr.columns.tolist()}")

    # Ensure numeric types for join
    df_raw['P'] = pd.to_numeric(df_raw['P'], errors='coerce')
    df_fdr['raw_p'] = pd.to_numeric(df_fdr['raw_p'], errors='coerce')

    # Merge
    # We keep all raw rows, but only those with a matching FDR entry get q-values.
    # Since FDR is derived from raw P-values, a match should exist for every row.
    df_merged = pd.merge(df_raw, df_fdr, left_on='P', right_on='raw_p', how='left')

    # Drop the redundant 'raw_p' column from the join, keep 'P'
    df_merged = df_merged.drop(columns=['raw_p'])

    # Sort by q_value (ascending) to put most significant results first.
    # Handle NaNs by placing them at the end.
    df_merged = df_merged.sort_values(by='q_value', ascending=True, na_position='last')

    # Write output
    df_merged.to_csv(output_path, sep='\t', index=False)

    print(f"Successfully merged and wrote {len(df_merged)} rows to {output_path}")

except Exception as e:
    print(f"Error during merge: {e}", file=sys.stderr)
    sys.exit(1)
PYTHON_SCRIPT

echo "Task T022 complete: $OUTPUT_FILE created."