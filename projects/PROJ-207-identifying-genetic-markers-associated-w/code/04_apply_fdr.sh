#!/bin/bash
# T022: Merge PLINK raw results with FDR-corrected results
# This script merges the raw GWAS statistics (from T017) with the
# Benjamini-Hochberg q-values (from T020) to produce the final artifact.
#
# Input:
#   data/interim/gwas_raw.tsv (Output of T017)
#   data/interim/gwas_fdr.tsv (Output of T020)
#
# Output:
#   data/processed/gwas_results_fdr.tsv

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

RAW_INPUT="${PROJECT_ROOT}/data/interim/gwas_raw.tsv"
FDR_INPUT="${PROJECT_ROOT}/data/interim/gwas_fdr.tsv"
OUTPUT_FILE="${PROJECT_ROOT}/data/processed/gwas_results_fdr.tsv"

echo "T022: Applying FDR merge to GWAS results..."

# Verify inputs exist
if [[ ! -f "$RAW_INPUT" ]]; then
    echo "ERROR: Raw GWAS input not found: $RAW_INPUT"
    echo "Did T017 (03_gwas.sh) run successfully?"
    exit 1
fi

if [[ ! -f "$FDR_INPUT" ]]; then
    echo "ERROR: FDR-corrected input not found: $FDR_INPUT"
    echo "Did T020 (utils/fdr_correction.py) run successfully?"
    exit 1
fi

# Ensure output directory exists
mkdir -p "$(dirname "$OUTPUT_FILE")"

# Merge logic using Python for robust column handling and preservation of metadata
python3 << 'PYTHON_SCRIPT'
import pandas as pd
import sys
import os

raw_path = os.environ.get('RAW_INPUT')
fdr_path = os.environ.get('FDR_INPUT')
output_path = os.environ.get('OUTPUT_FILE')

try:
    # Load raw results
    # Expected columns: SNP, CHRM, POS, A1, A2, TEST, ODDSRATIO, BETA, SE, P, N
    df_raw = pd.read_csv(raw_path, sep='\t')

    # Load FDR results
    # Expected columns: rank, raw_p, q_value, significant
    df_fdr = pd.read_csv(fdr_path, sep='\t')

    if df_raw.empty:
        print("ERROR: Raw GWAS data is empty. Cannot merge.", file=sys.stderr)
        sys.exit(1)

    if df_fdr.empty:
        print("ERROR: FDR data is empty. Cannot merge.", file=sys.stderr)
        sys.exit(1)

    # Ensure the raw p-value column in the raw file matches the FDR input
    # The FDR script outputs 'raw_p', the raw file usually has 'P' or 'P-value'
    p_col_name = 'P'
    if p_col_name not in df_raw.columns and 'P-VALUE' in df_raw.columns:
        p_col_name = 'P-VALUE'
    elif p_col_name not in df_raw.columns and 'p' in df_raw.columns:
        p_col_name = 'p'
    
    if p_col_name not in df_raw.columns:
        print(f"ERROR: Could not find p-value column in raw file. Columns: {list(df_raw.columns)}", file=sys.stderr)
        sys.exit(1)

    # Merge on the p-value. 
    # Note: Floating point comparison can be risky, but for this pipeline 
    # the FDR script reads the exact same file and sorts by this column.
    # We will merge on the p-value to align the rows.
    
    # To ensure exact matching, we convert p-values to string with high precision
    # or rely on the fact that they come from the same sorted stream.
    # Given the FDR script reads the file directly, the order (rank) corresponds 
    # to the sorted order of the raw file. 
    
    # Strategy: Sort raw file by P-value ascending, reset index, 
    # then assign FDR columns based on index match (since FDR is also sorted by P).
    
    df_raw_sorted = df_raw.sort_values(by=p_col_name, ascending=True).reset_index(drop=True)
    
    # Verify counts match (they should if FDR was run on this exact file)
    if len(df_raw_sorted) != len(df_fdr):
        print(f"WARNING: Row count mismatch. Raw: {len(df_raw_sorted)}, FDR: {len(df_fdr)}. "
              f"This may indicate the FDR script processed a different subset.", file=sys.stderr)
        # We proceed with the minimum length to avoid index errors, but log the warning
        min_len = min(len(df_raw_sorted), len(df_fdr))
        df_raw_sorted = df_raw_sorted.head(min_len)
        df_fdr = df_fdr.head(min_len)

    # Concatenate columns
    # We drop the 'raw_p' from FDR to avoid duplication, keeping the original 'P' column
    df_fdr_clean = df_fdr.drop(columns=['raw_p'])
    
    df_final = pd.concat([df_raw_sorted, df_fdr_clean], axis=1)

    # Drop the redundant 'raw_p' column from the join, keep 'P'
    df_merged = df_merged.drop(columns=['raw_p'])

    # Write final result
    df_final.to_csv(output_path, sep='\t', index=False)
    
    print(f"Successfully merged results to {output_path}")
    print(f"Total SNPs in final output: {len(df_final)}")
    print(f"Significant SNPs (q < 0.05): {df_final['significant'].sum()}")

except Exception as e:
    print(f"ERROR during merge: {e}", file=sys.stderr)
    sys.exit(1)
PYTHON_SCRIPT

export RAW_INPUT FDR_INPUT OUTPUT_FILE
python3 << 'PYTHON_SCRIPT'
import pandas as pd
import sys
import os

raw_path = os.environ.get('RAW_INPUT')
fdr_path = os.environ.get('FDR_INPUT')
output_path = os.environ.get('OUTPUT_FILE')

try:
    df_raw = pd.read_csv(raw_path, sep='\t')
    df_fdr = pd.read_csv(fdr_path, sep='\t')

    if df_raw.empty:
        print("ERROR: Raw GWAS data is empty.", file=sys.stderr)
        sys.exit(1)
    if df_fdr.empty:
        print("ERROR: FDR data is empty.", file=sys.stderr)
        sys.exit(1)

    p_col_name = 'P'
    if p_col_name not in df_raw.columns:
        if 'P-VALUE' in df_raw.columns: p_col_name = 'P-VALUE'
        elif 'p' in df_raw.columns: p_col_name = 'p'
        else:
            print(f"ERROR: P-value column not found in {raw_path}", file=sys.stderr)
            sys.exit(1)

    df_raw_sorted = df_raw.sort_values(by=p_col_name, ascending=True).reset_index(drop=True)
    
    if len(df_raw_sorted) != len(df_fdr):
        print(f"WARNING: Row count mismatch. Raw: {len(df_raw_sorted)}, FDR: {len(df_fdr)}.", file=sys.stderr)
        min_len = min(len(df_raw_sorted), len(df_fdr))
        df_raw_sorted = df_raw_sorted.head(min_len)
        df_fdr = df_fdr.head(min_len)

    df_fdr_clean = df_fdr.drop(columns=['raw_p'])
    df_final = pd.concat([df_raw_sorted, df_fdr_clean], axis=1)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df_final.to_csv(output_path, sep='\t', index=False)
    
    print(f"SUCCESS: Output written to {output_path}")
    print(f"Significant SNPs: {df_final['significant'].sum()}")

except Exception as e:
    print(f"ERROR: {e}", file=sys.stderr)
    sys.exit(1)
PYTHON_SCRIPT