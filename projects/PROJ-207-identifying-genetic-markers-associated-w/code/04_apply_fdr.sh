#!/usr/bin/env bash
#
# T022 – Merge PLINK raw GWAS results with FDR‑corrected results.
#
# This script reads:
#   data/interim/gwas_raw.tsv          – raw PLINK output (columns: SNP, CHR, POS, P, Odds_Ratio, …)
#   data/interim/gwas_raw_fdr.tsv      – same rows with an added q_value column (produced by T020)
#
# It merges on the SNP identifier and writes the final artifact:
#   data/processed/gwas_results_fdr.tsv
#
# Required columns in the final file:
#   SNP, CHR, POS, P, Odds_Ratio, q_value
#
# The script aborts with a non‑zero exit code if inputs are missing or the merge fails.

set -euo pipefail

RAW="data/interim/gwas_raw.tsv"
FDR="data/interim/gwas_raw_fdr.tsv"
OUT="data/processed/gwas_results_fdr.tsv"

# Verify input files exist
if [[ ! -f "$RAW" ]]; then
    echo "Error: Raw GWAS results not found at $RAW" >&2
    exit 1
fi

if [[ ! -f "$FDR" ]]; then
    echo "Error: FDR‑corrected results not found at $FDR" >&2
    exit 1
fi

# Ensure the output directory exists
mkdir -p "$(dirname "$OUT")"

# Perform the merge using a short Python snippet (pandas is a project dependency)
python - <<'PY' "$RAW" "$FDR" "$OUT"
import sys
import pandas as pd

raw_path, fdr_path, out_path = sys.argv[1:4]

# Load input tables
raw = pd.read_csv(raw_path, sep='\t')
fdr = pd.read_csv(fdr_path, sep='\t')

# Merge on SNP, retaining the q_value from the FDR file
merged = pd.merge(raw, fdr[['SNP', 'q_value']], on='SNP', how='inner')

# Verify required columns are present
required = ['SNP', 'CHR', 'POS', 'P', 'Odds_Ratio', 'q_value']
missing = set(required) - set(merged.columns)
if missing:
    raise ValueError(f"Missing required columns after merge: {missing}")

# Order columns as specified
merged = merged[required]

# Write final TSV
merged.to_csv(out_path, sep='\t', index=False)
PY

echo "Successfully merged GWAS results with FDR correction."
echo "Output written to $OUT"