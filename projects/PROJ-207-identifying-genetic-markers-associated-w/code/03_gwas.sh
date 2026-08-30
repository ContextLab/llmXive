#!/bin/bash
# T017: Execute PLINK logistic regression for GWAS
# Output: data/interim/gwas_raw.tsv
# Note: FDR correction is handled by T020 (fdr_correction.py)

set -euo pipefail

# Configuration
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( dirname "$SCRIPT_DIR" )"
CODE_DIR="$PROJECT_ROOT/code"
DATA_DIR="$PROJECT_ROOT/data"
INTERIM_DIR="$DATA_DIR/interim"
PROCESSED_DIR="$DATA_DIR/processed"

# Ensure output directory exists
mkdir -p "$INTERIM_DIR"

# Define input files based on previous pipeline steps (T015, T016, T064)
# T015: VCF to PLINK conversion -> data/interim/genotype
# T016: Preprocess phenotype -> data/interim/phenotypes_cleaned
# T064: Collinearity diagnostics -> data/interim/covariates.csv (or similar)

# Check for required input files
BED_FILE="$INTERIM_DIR/genotype.bed"
BIM_FILE="$INTERIM_DIR/genotype.bim"
FAM_FILE="$INTERIM_DIR/genotype.fam"
PHENO_FILE="$INTERIM_DIR/phenotypes_cleaned.pheno"
COV_FILE="$INTERIM_DIR/covariates.csv"

if [[ ! -f "$BED_FILE" ]] || [[ ! -f "$BIM_FILE" ]] || [[ ! -f "$FAM_FILE" ]]; then
    echo "ERROR: PLINK binary files not found in $INTERIM_DIR. Did T015 (vcf_to_plink) run successfully?"
    exit 1
fi

if [[ ! -f "$PHENO_FILE" ]]; then
    echo "ERROR: Phenotype file not found at $PHENO_FILE. Did T016 (preprocess_phenotype) run successfully?"
    exit 1
fi

if [[ ! -f "$COV_FILE" ]]; then
    echo "WARNING: Covariate file not found at $COV_FILE. Running GWAS without covariates. (T064 may not have run)"
    COV_FLAG=""
else
    COV_FLAG="--covar $COV_FILE"
fi

OUTPUT_PREFIX="$INTERIM_DIR/gwas_raw"
LOG_FILE="$INTERIM_DIR/gwas_execution.log"

echo "Starting PLINK logistic regression at $(date)" | tee "$LOG_FILE"
echo "Input Bed: $BED_FILE" | tee -a "$LOG_FILE"
echo "Input Phenotype: $PHENO_FILE" | tee -a "$LOG_FILE"
if [[ -n "$COV_FLAG" ]]; then
    echo "Input Covariates: $COV_FILE" | tee -a "$LOG_FILE"
fi

# Execute PLINK 2.0 logistic regression
# Using --logistic hide-covar to get standard output
# --covar-name can be used if specific columns are needed, but default is all
# Assuming phenotype column 1 is the target (CCD status)

plink2 \
    --bfile "$INTERIM_DIR/genotype" \
    --pheno "$PHENO_FILE" \
    --pheno-name CCD_Status \
    --covar "$COV_FILE" \
    --logistic hide-covar \
    --out "$OUTPUT_PREFIX" \
    2>&1 | tee -a "$LOG_FILE"

# Verify output
EXPECTED_OUTPUT="$OUTPUT_PREFIX.logistic"
if [[ -f "$EXPECTED_OUTPUT" ]]; then
    # PLINK outputs .logistic file. We need to rename/move to gwas_raw.tsv as per spec.
    # The spec asks for `data/interim/gwas_raw.tsv`.
    mv "$EXPECTED_OUTPUT" "$INTERIM_DIR/gwas_raw.tsv"
    echo "Successfully wrote raw association statistics to $INTERIM_DIR/gwas_raw.tsv" | tee -a "$LOG_FILE"
    
    # Verify file is not empty
    if [[ ! -s "$INTERIM_DIR/gwas_raw.tsv" ]]; then
        echo "ERROR: Output file $INTERIM_DIR/gwas_raw.tsv is empty." | tee -a "$LOG_FILE"
        exit 1
    fi
else
    echo "ERROR: PLINK did not produce the expected output file." | tee -a "$LOG_FILE"
    ls -la "$INTERIM_DIR" | tee -a "$LOG_FILE"
    exit 1
fi

echo "GWAS execution completed successfully at $(date)" | tee -a "$LOG_FILE"