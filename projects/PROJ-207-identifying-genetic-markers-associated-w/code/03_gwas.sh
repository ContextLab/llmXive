#!/bin/bash
set -e

# T017: Execute PLINK logistic regression for GWAS
# Input: data/processed/model_config.yaml (from T046)
#        data/processed/phenotypes_cleaned.fam (from T016)
#        data/processed/pruned_genotypes.bed (from T016)
# Output: data/interim/gwas_raw.tsv

echo "Starting GWAS execution (T017)..."

# Verify required inputs exist
if [ ! -f "data/processed/model_config.yaml" ]; then
    echo "ERROR: data/processed/model_config.yaml not found. Run T046 first."
    exit 1
fi

if [ ! -f "data/processed/phenotypes_cleaned.fam" ]; then
    echo "ERROR: data/processed/phenotypes_cleaned.fam not found. Run T016 first."
    exit 1
fi

if [ ! -f "data/processed/pruned_genotypes.bed" ]; then
    echo "ERROR: data/processed/pruned_genotypes.bed not found. Run T016 first."
    exit 1
fi

# Read model configuration
STRATEGY=$(grep "^strategy:" data/processed/model_config.yaml | awk '{print $2}')
echo "Detected model strategy: $STRATEGY"

COVAR_FILE=""
if [ "$STRATEGY" == "Covariates" ]; then
    COVAR_FILE="data/processed/phenotypes_cleaned.pheno"
    if [ ! -f "$COVAR_FILE" ]; then
        echo "ERROR: Covariate strategy selected but $COVAR_FILE not found."
        exit 1
    fi
    echo "Using covariates from: $COVAR_FILE"
elif [ "$STRATEGY" == "PCA" ]; then
    COVAR_FILE="data/processed/pruned_genotypes.eigenvec"
    if [ ! -f "$COVAR_FILE" ]; then
        echo "ERROR: PCA strategy selected but PCA file not found. Run PLINK PCA first."
        exit 1
    fi
    echo "Using PCA components from: $COVAR_FILE"
else
    echo "ERROR: Unknown strategy in model_config.yaml: $STRATEGY"
    exit 1
fi

# Define output paths
OUTPUT_PREFIX="data/interim/gwas_raw"

echo "Running PLINK2 logistic regression..."
echo "Input: data/processed/pruned_genotypes"
echo "Phenotype: data/processed/phenotypes_cleaned.fam"
echo "Covariates: $COVAR_FILE"
echo "Output: $OUTPUT_PREFIX"

# Execute PLINK2
# --logistic hide-covar: Run logistic regression, hide covariate details in output
# --ci 0.95: Calculate 95% confidence intervals for OR
# --covar: Provide covariate file
# --pheno: Explicitly specify phenotype file (though .fam is often used, explicit is safer)
# --family: Specify family structure (0=unrelated)
plink2 \
    --bfile data/processed/pruned_genotypes \
    --pheno data/processed/phenotypes_cleaned.fam \
    --family 0 \
    --covar "$COVAR_FILE" \
    --logistic hide-covar \
    --ci 0.95 \
    --out "$OUTPUT_PREFIX"

# Post-processing: Ensure column names match schema (Odds_Ratio instead of OR)
# PLINK2 outputs 'OR' by default. We need to rename it to 'Odds_Ratio' for downstream compatibility.
echo "Post-processing GWAS output to match schema..."

INPUT_FILE="${OUTPUT_PREFIX}.assoc.logistic"
if [ ! -f "$INPUT_FILE" ]; then
    echo "ERROR: PLINK2 did not produce expected output file: $INPUT_FILE"
    exit 1
fi

OUTPUT_TSV="${OUTPUT_PREFIX}.tsv"

# Use awk to rename the column 'OR' to 'Odds_Ratio'
# This assumes the header line contains 'OR' as the 8th column (standard PLINK logistic output)
# If the column index varies, a more robust header scan is needed.
# Standard PLINK2 logistic header: CHR SNP BP A1 TEST NMISS OR SE P
awk 'BEGIN {FS="\t"; OFS="\t"} 
     NR==1 {
         for(i=1; i<=NF; i++) {
             if($i == "OR") $i = "Odds_Ratio"
         }
         print
         next
     }
     {print}' "$INPUT_FILE" > "$OUTPUT_TSV"

# Verify output
if [ -f "$OUTPUT_TSV" ]; then
    echo "SUCCESS: GWAS raw results written to $OUTPUT_TSV"
    echo "Columns:"
    head -1 "$OUTPUT_TSV"
else
    echo "ERROR: Failed to write output file $OUTPUT_TSV"
    exit 1
fi

echo "T017 completed successfully."
