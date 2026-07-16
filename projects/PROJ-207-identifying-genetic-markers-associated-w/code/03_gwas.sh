#!/bin/bash
# code/03_gwas.sh
# Executes PLINK logistic regression for GWAS analysis with covariates.
#
# Usage:
#   ./code/03_gwas.sh <plink_prefix> <phenotype_file> <covariate_file> <output_prefix>
#
# Arguments:
#   plink_prefix: Prefix for PLINK binary files (.bed, .bim, .fam)
#   phenotype_file: Path to phenotype file (.pheno)
#   covariate_file: Path to covariate file (.covar)
#   output_prefix: Prefix for output files
#
# Environment Variables:
#   PLINK_THREADS: Number of threads for PLINK (default: 4)
#   LOGISTIC_MODEL: Logistic regression model type (default: firth)

set -euo pipefail

# Configuration with defaults
PLINK_THREADS="${PLINK_THREADS:-4}"
LOGISTIC_MODEL="${LOGISTIC_MODEL:-firth}"

# Validate arguments
if [ $# -ne 4 ]; then
    echo "Usage: $0 <plink_prefix> <phenotype_file> <covariate_file> <output_prefix>" >&2
    echo "  plink_prefix: Prefix for PLINK binary files" >&2
    echo "  phenotype_file: Path to phenotype file" >&2
    echo "  covariate_file: Path to covariate file" >&2
    echo "  output_prefix: Prefix for output files" >&2
    exit 1
fi

PLINK_PREFIX="$1"
PHENOTYPE_FILE="$2"
COVARIATE_FILE="$3"
OUTPUT_PREFIX="$4"

# Validate input files exist
if [ ! -f "${PLINK_PREFIX}.bed" ]; then
    echo "ERROR: PLINK BED file not found: ${PLINK_PREFIX}.bed" >&2
    exit 1
fi

if [ ! -f "${PLINK_PREFIX}.bim" ]; then
    echo "ERROR: PLINK BIM file not found: ${PLINK_PREFIX}.bim" >&2
    exit 1
fi

if [ ! -f "${PLINK_PREFIX}.fam" ]; then
    echo "ERROR: PLINK FAM file not found: ${PLINK_PREFIX}.fam" >&2
    exit 1
fi

if [ ! -f "$PHENOTYPE_FILE" ]; then
    echo "ERROR: Phenotype file not found: $PHENOTYPE_FILE" >&2
    exit 1
fi

if [ ! -f "$COVARIATE_FILE" ]; then
    echo "ERROR: Covariate file not found: $COVARIATE_FILE" >&2
    exit 1
fi

# Create output directory if it doesn't exist
OUTPUT_DIR=$(dirname "$OUTPUT_PREFIX")
mkdir -p "$OUTPUT_DIR"

# Execute PLINK logistic regression
RAW_OUTPUT="${OUTPUT_PREFIX}_raw.logistic"
echo "Running PLINK logistic regression with covariates"

plink \
    --bfile "$PLINK_PREFIX" \
    --logistic hide-covar $LOGISTIC_MODEL \
    --covar "$COVARIATE_FILE" \
    --pheno "$PHENOTYPE_FILE" \
    --covar-name Geographic_Region,Sampling_Year,Varroa_Load \
    --threads "$PLINK_THREADS" \
    --out "$RAW_OUTPUT"

# Convert PLINK output to TSV format
RAW_TSV="${OUTPUT_PREFIX}_raw.tsv"
if [ -f "${RAW_OUTPUT}.assoc.logistic" ]; then
    # PLINK 1.9/2.0 output format
    cp "${RAW_OUTPUT}.assoc.logistic" "$RAW_TSV"
elif [ -f "${RAW_OUTPUT}.logistic" ]; then
    # Alternative output format
    cp "${RAW_OUTPUT}.logistic" "$RAW_TSV"
else
    echo "ERROR: PLINK did not generate expected output files" >&2
    ls -la "${RAW_OUTPUT}"* >&2
    exit 1
fi

# Generate summary statistics
TOTAL_SNPS=$(tail -n +2 "$RAW_TSV" | wc -l)
SIGNIFICANT_SNPS=$(tail -n +2 "$RAW_TSV" | awk -v p=5e-8 '$P < p {count++} END {print count+0}')

SUMMARY_FILE="${OUTPUT_PREFIX}_summary.txt"
cat > "$SUMMARY_FILE" <<EOF
GWAS Analysis Summary
=====================
Input:
  PLINK Prefix: $PLINK_PREFIX
  Phenotype File: $PHENOTYPE_FILE
  Covariate File: $COVARIATE_FILE
  Model: $LOGISTIC_MODEL
  Threads: $PLINK_THREADS

Covariates Used:
  - Geographic_Region
  - Sampling_Year
  - Varroa_Load

Results:
  Total SNPs Analyzed: $TOTAL_SNPS
  Significant SNPs (p < 5e-8): $SIGNIFICANT_SNPS

Output Files:
  Raw TSV: $RAW_TSV
  Summary: $SUMMARY_FILE

Note: This output contains raw association statistics.
FDR correction must be applied separately using code/04_apply_fdr.sh.
EOF

echo "GWAS pipeline complete. Summary: $SUMMARY_FILE"
echo "Raw results: $RAW_TSV"