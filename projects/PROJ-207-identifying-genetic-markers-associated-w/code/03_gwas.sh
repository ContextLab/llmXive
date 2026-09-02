#!/bin/bash
# T017: Execute PLINK logistic regression for GWAS
# Output: data/interim/gwas_raw.tsv
#
# Prerequisites:
#   - T015: VCF to PLINK conversion (produces .bed, .bim, .fam)
#   - T016: Phenotype preprocessing (produces covariates)
#   - T046: Mandatory covariates defined (geographic region, sampling year, Varroa count)
#
# This script executes PLINK logistic regression with mandatory covariates.
# It does NOT include FDR logic (handled by T020).

set -euo pipefail

# Configuration
PLINK_BIN="${PLINK_BIN:-plink}"
INPUT_PREFIX="${INPUT_PREFIX:-data/interim/harmonized}"
COVARIATE_FILE="${COVARIATE_FILE:-data/interim/covariates.tsv}"
OUTPUT_FILE="${OUTPUT_FILE:-data/interim/gwas_raw.tsv}"
LOG_FILE="${LOG_FILE:-data/interim/gwas_run.log}"

# Validate inputs exist
if [[ ! -f "${INPUT_PREFIX}.bed" ]]; then
    echo "ERROR: Input PLINK files not found. Expected ${INPUT_PREFIX}.bed"
    echo "Run T015 (vcf_to_plink) and T016 (preprocess_phenotype) first."
    exit 1
fi

if [[ ! -f "${COVARIATE_FILE}" ]]; then
    echo "ERROR: Covariate file not found: ${COVARIATE_FILE}"
    echo "Run T016 (preprocess_phenotype) first to generate covariates."
    exit 1
fi

echo "Starting PLINK logistic regression at $(date)"
echo "Input prefix: ${INPUT_PREFIX}"
echo "Covariate file: ${COVARIATE_FILE}"
echo "Output file: ${OUTPUT_FILE}"

# Execute PLINK logistic regression with mandatory covariates
# --logistic: Perform logistic regression
# --covar: Include covariates (geographic region, sampling year, Varroa count)
# --covar-name: Explicitly name the mandatory covariates
# --out: Output prefix
# --threads: Use multiple threads if available
# --allow-no-sex: Allow samples without sex information
# --hide-covar: Hide covariate coefficients in output (cleaner raw stats)

${PLINK_BIN} \
    --bfile "${INPUT_PREFIX}" \
    --logistic \
    --covar "${COVARIATE_FILE}" \
    --covar-name REGION YEAR VARROA_COUNT \
    --out "${OUTPUT_FILE%.*}" \
    --threads 4 \
    --allow-no-sex \
    --hide-covar \
    2>&1 | tee "${LOG_FILE}"

# Verify output was created
if [[ ! -f "${OUTPUT_FILE}" ]]; then
    # PLINK might output with different extension depending on version
    # Check for .assoc.logistic which is common output
    if [[ -f "${OUTPUT_FILE%.*}.assoc.logistic" ]]; then
        mv "${OUTPUT_FILE%.*}.assoc.logistic" "${OUTPUT_FILE}"
        echo "Renamed output file to ${OUTPUT_FILE}"
    else
        echo "ERROR: PLINK did not produce expected output file: ${OUTPUT_FILE}"
        echo "Check log file for errors: ${LOG_FILE}"
        exit 1
    fi
fi

# Validate output contains expected columns
if ! head -1 "${OUTPUT_FILE}" | grep -q "CHR\|SNP\|P"; then
    echo "ERROR: Output file ${OUTPUT_FILE} does not contain expected GWAS columns (CHR, SNP, P)"
    echo "File content preview:"
    head -5 "${OUTPUT_FILE}"
    exit 1
fi

# Count results
RESULT_COUNT=$(tail -n +2 "${OUTPUT_FILE}" | wc -l)
echo "SUCCESS: GWAS completed. Found ${RESULT_COUNT} SNPs tested."
echo "Output written to: ${OUTPUT_FILE}"
echo "Log written to: ${LOG_FILE}"
echo "Completed at $(date)"

# Verify the file is non-empty and has data
if [[ ${RESULT_COUNT} -eq 0 ]]; then
    echo "WARNING: No SNPs were tested. Check input data and filtering."
    exit 0  # Not a fatal error, but worth noting
fi

exit 0