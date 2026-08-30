#!/bin/bash
# T017: Execute PLINK logistic regression for GWAS
# Outputs raw association statistics to data/interim/gwas_raw.tsv
# Does NOT include FDR logic (handled by T020)

set -euo pipefail

# Paths
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CODE_DIR="${PROJECT_ROOT}/code"
DATA_DIR="${PROJECT_ROOT}/data"
INTERIM_DIR="${DATA_DIR}/interim"
PROCESSED_DIR="${DATA_DIR}/processed"

# Input files (produced by previous steps)
# T015: VCF to PLINK conversion -> data/interim/gwas_cleaned
# T016: Phenotype preprocessing -> data/interim/phenotypes_cleaned
# T046: Covariates (encoded) -> typically merged into .pheno or separate file
# T064: Collinearity diagnostics passed (assumed)

PLINK_PREFIX="${INTERIM_DIR}/gwas_cleaned"
PHENO_FILE="${INTERIM_DIR}/phenotypes_cleaned.pheno"
COV_FILE="${INTERIM_DIR}/covariates_cleaned.cov"
OUTPUT_PREFIX="${INTERIM_DIR}/gwas_raw"

# Check prerequisites
if [ ! -f "${PLINK_PREFIX}.bed" ]; then
    echo "ERROR: PLINK binary file not found: ${PLINK_PREFIX}.bed"
    echo "Ensure T015 (vcf_to_plink) and T016 (preprocess_phenotype) have completed successfully."
    exit 1
fi

if [ ! -f "${PHENO_FILE}" ]; then
    echo "ERROR: Phenotype file not found: ${PHENO_FILE}"
    exit 1
fi

if [ ! -f "${COV_FILE}" ]; then
    echo "ERROR: Covariate file not found: ${COV_FILE}"
    echo "Ensure T016 (preprocess_phenotype) generated covariates."
    exit 1
fi

# Ensure output directory exists
mkdir -p "${INTERIM_DIR}"

# Execute PLINK logistic regression
# --logistic: Perform logistic regression for binary trait
# --covar: Include covariates (geographic region, sampling year, Varroa count)
# --covar-name: Explicitly specify covariate columns if needed (optional, PLINK auto-detects header)
# --out: Output prefix
# --adjust: Output basic adjustments (optional, but good for debugging)
# --ci: Confidence intervals for odds ratios (optional)

echo "Starting PLINK logistic regression..."
echo "Input: ${PLINK_PREFIX}"
echo "Phenotype: ${PHENO_FILE}"
echo "Covariates: ${COV_FILE}"
echo "Output: ${OUTPUT_PREFIX}"

plink2 \
    --bfile "${PLINK_PREFIX}" \
    --logistic hide-covar \
    --covar "${COV_FILE}" \
    --pheno "${PHENO_FILE}" \
    --pheno-name "CCD_Status" \
    --out "${OUTPUT_PREFIX}" \
    2>&1 | tee "${INTERIM_DIR}/gwas_run.log"

# Verify output
if [ -f "${OUTPUT_PREFIX}.assoc.logistic" ]; then
    echo "SUCCESS: Raw association statistics written to ${OUTPUT_PREFIX}.assoc.logistic"
    # The task requires output to `data/interim/gwas_raw.tsv`
    # PLINK outputs `*.assoc.logistic`. We move/rename it to match the spec.
    mv "${OUTPUT_PREFIX}.assoc.logistic" "${OUTPUT_PREFIX}.tsv"
    echo "Renamed output to: ${OUTPUT_PREFIX}.tsv"
else
    echo "ERROR: PLINK did not produce the expected output file: ${OUTPUT_PREFIX}.assoc.logistic"
    exit 1
fi

echo "T017 completed successfully."
