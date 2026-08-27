#!/bin/bash
# code/04_apply_fdr.sh
# Merges PLINK raw results (T017) with FDR-corrected results (T020)
# into the final artifact: data/processed/gwas_results_fdr.tsv

set -e

RAW_INPUT="data/interim/gwas_raw.tsv"
FDR_INPUT="data/interim/gwas_raw_fdr.tsv"
OUTPUT_FILE="data/processed/gwas_results_fdr.tsv"

echo "Starting FDR merge process..."

# Check input files exist
if [ ! -f "$RAW_INPUT" ]; then
    echo "ERROR: Raw GWAS results file not found: $RAW_INPUT"
    echo "Please ensure T017 (03_gwas.py) has completed successfully."
    exit 1
fi

if [ ! -f "$FDR_INPUT" ]; then
    echo "ERROR: FDR-corrected results file not found: $FDR_INPUT"
    echo "Please ensure T020 (utils/fdr_correction.py) has completed successfully."
    exit 1
fi

echo "Merging $RAW_INPUT and $FDR_INPUT..."

# Use Python to merge on 'SNP' column to ensure robust handling of delimiters and types
python3 << 'EOF'
import pandas as pd
import sys
import os

raw_path = "data/interim/gwas_raw.tsv"
fdr_path = "data/interim/gwas_raw_fdr.tsv"
output_path = "data/processed/gwas_results_fdr.tsv"

try:
    # Load raw results
    df_raw = pd.read_csv(raw_path, sep='\t')
    
    # Load FDR results
    df_fdr = pd.read_csv(fdr_path, sep='\t')

    # Validate required columns exist in raw
    required_raw_cols = ['SNP', 'CHR', 'POS', 'P', 'Odds_Ratio']
    missing_raw = [c for c in required_raw_cols if c not in df_raw.columns]
    if missing_raw:
  print(f"ERROR: Raw file missing columns: {missing_raw}")
  sys.exit(1)

    # Validate required columns exist in FDR (specifically q_value)
    if 'q_value' not in df_fdr.columns:
  print("ERROR: FDR file missing 'q_value' column.")
  sys.exit(1)

    # Merge on 'SNP'
    # We take all columns from raw, and only append 'q_value' from fdr to avoid duplicates
    df_merged = df_raw.merge(
  df_fdr[['SNP', 'q_value']], 
  on='SNP', 
  how='left'
    )

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Write final artifact
    # Ensure column order matches specification: SNP, CHR, POS, P, Odds_Ratio, q_value
    final_cols = ['SNP', 'CHR', 'POS', 'P', 'Odds_Ratio', 'q_value']
    # Filter to only these columns if extra exist, or reorder
    existing_cols = [c for c in final_cols if c in df_merged.columns]
    
    # If any mandatory column is missing after merge (e.g. q_value didn't match), log warning but proceed
    missing_final = [c for c in final_cols if c not in existing_cols]
    if missing_final:
  print(f"WARNING: Final output missing columns: {missing_final}. Proceeding with available data.")

    df_merged[existing_cols].to_csv(output_path, sep='\t', index=False)

    print(f"Successfully wrote merged results to {output_path}")
    print(f"Total rows: {len(df_merged)}, Columns: {list(df_merged.columns)}")

except Exception as e:
    print(f"ERROR during merge: {str(e)}")
    sys.exit(1)
EOF

if [ $? -eq 0 ]; then
    echo "FDR merge completed successfully."
    echo "Output artifact: $OUTPUT_FILE"
else
    echo "FDR merge failed."
    exit 1
fi