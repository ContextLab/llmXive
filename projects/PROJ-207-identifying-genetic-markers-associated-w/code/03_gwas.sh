#!/bin/bash
# T017: Execute PLINK logistic regression with covariates
# Output: data/interim/gwas_raw.tsv
#
# This script runs the GWAS step (FR-004). It assumes:
# 1. Data has been converted to PLINK format (bed/bim/fam) in data/processed/
# 2. Covariates are available in data/processed/phenotypes_cleaned.pheno
# 3. Sample size >= 80 (enforced by T043 prior to this step)

set -e

# Define paths relative to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

INPUT_PREFIX="${PROJECT_ROOT}/data/processed/colony_gwas"
PHENO_FILE="${PROJECT_ROOT}/data/processed/phenotypes_cleaned.pheno"
FAM_FILE="${PROJECT_ROOT}/data/processed/phenotypes_cleaned.fam"
OUTPUT_FILE="${PROJECT_ROOT}/data/interim/gwas_raw.tsv"
LOG_FILE="${PROJECT_ROOT}/data/interim/gwas_run.log"

echo "Starting GWAS execution at $(date)" | tee "$LOG_FILE"
echo "Input prefix: $INPUT_PREFIX" | tee -a "$LOG_FILE"
echo "Phenotype file: $PHENO_FILE" | tee -a "$LOG_FILE"
echo "Output file: $OUTPUT_FILE" | tee -a "$LOG_FILE"

# Check that input files exist
if [[ ! -f "${INPUT_PREFIX}.bed" ]]; then
    echo "ERROR: Input .bed file not found: ${INPUT_PREFIX}.bed" | tee -a "$LOG_FILE"
    exit 1
fi
if [[ ! -f "${INPUT_PREFIX}.bim" ]]; then
    echo "ERROR: Input .bim file not found: ${INPUT_PREFIX}.bim" | tee -a "$LOG_FILE"
    exit 1
fi
if [[ ! -f "${INPUT_PREFIX}.fam" ]]; then
    echo "ERROR: Input .fam file not found: ${INPUT_PREFIX}.fam" | tee -a "$LOG_FILE"
    exit 1
fi
if [[ ! -f "$PHENO_FILE" ]]; then
    echo "ERROR: Phenotype file not found: $PHENO_FILE" | tee -a "$LOG_FILE"
    exit 1
fi

# Verify sample count matches between FAM and PHENO
FAM_COUNT=$(tail -n +2 "$FAM_FILE" | wc -l)
PHENO_COUNT=$(tail -n +2 "$PHENO_FILE" | wc -l)

if [[ "$FAM_COUNT" -ne "$PHENO_COUNT" ]]; then
    echo "ERROR: Sample count mismatch. FAM has $FAM_COUNT, PHENO has $PHENO_COUNT" | tee -a "$LOG_FILE"
    exit 1
fi

echo "Sample count verified: $FAM_COUNT" | tee -a "$LOG_FILE"

# Run PLINK2 logistic regression
# --logistic: Perform logistic regression
# --covar: Include covariates from the phenotype file
# --covar-name: Specify which columns in the covar file to use as covariates
#   (Columns 3, 4, 5 correspond to geographic region, sampling year, Varroa load based on T016)
# --out: Output prefix
# Note: We use the phenotype file as the covariate file because T016 outputs
# the cleaned covariates there. The first two columns (FID, IID) are used for matching.

echo "Executing PLINK2 logistic regression..." | tee -a "$LOG_FILE"

plink2 \
    --bfile "$INPUT_PREFIX" \
    --logistic \
    --covar "$PHENO_FILE" \
    --covar-name C3,C4,C5 \
    --out "${OUTPUT_FILE%.*}" \
    2>&1 | tee -a "$LOG_FILE"

# PLINK outputs .assoc.logistic by default. Move/rename to the expected output path.
PLINK_OUTPUT="${OUTPUT_FILE%.*}.assoc.logistic"

if [[ -f "$PLINK_OUTPUT" ]]; then
    mv "$PLINK_OUTPUT" "$OUTPUT_FILE"
    echo "GWAS complete. Results written to: $OUTPUT_FILE" | tee -a "$LOG_FILE"
    echo "First 5 lines of output:" | tee -a "$LOG_FILE"
    head -n 5 "$OUTPUT_FILE" | tee -a "$LOG_FILE"
else
    echo "ERROR: PLINK did not produce the expected output file: $PLINK_OUTPUT" | tee -a "$LOG_FILE"
    exit 1
fi

echo "Execution finished at $(date)" | tee -a "$LOG_FILE"