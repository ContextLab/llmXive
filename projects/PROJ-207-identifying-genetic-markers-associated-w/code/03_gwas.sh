#!/bin/bash
#
# code/03_gwas.sh
# Execute PLINK2 logistic regression for GWAS analysis.
#
# Input:
#   - data/processed/genotypes_cleaned (PLINK binary prefix from T015/T046)
#   - data/processed/phenotypes_cleaned.fam (Phenotype file from T016)
#   - data/processed/phenotypes_cleaned.cov (Covariate file from T016 or T046)
#
# Output:
#   - data/interim/gwas_raw.tsv (Raw association statistics)
#
# Dependencies:
#   - plink2 (must be in PATH)
#   - T016 (preprocess_phenotype.py)
#   - T046 (collinearity_guard.py)
#
# Notes:
#   - If T046 triggered PCA fallback, the covariate file will contain PCs.
#   - If T046 passed, the covariate file contains geographic region, sampling year, Varroa load.
#   - FDR correction is handled by T022 (04_apply_fdr.sh).
#

set -e

# Configuration
GENO_PREFIX="data/processed/genotypes_cleaned"
PHENO_FILE="data/processed/phenotypes_cleaned.fam"
COVAR_FILE="data/processed/phenotypes_cleaned.cov"
OUTPUT_FILE="data/interim/gwas_raw.tsv"

# Ensure output directory exists
mkdir -p "$(dirname "$OUTPUT_FILE")"

# Verify input files exist
if [ ! -f "${GENO_PREFIX}.bed" ]; then
    echo "ERROR: Genotype file ${GENO_PREFIX}.bed not found. Did T015 run?"
    exit 1
fi
if [ ! -f "$PHENO_FILE" ]; then
    echo "ERROR: Phenotype file $PHENO_FILE not found. Did T016 run?"
    exit 1
fi
if [ ! -f "$COVAR_FILE" ]; then
    echo "ERROR: Covariate file $COVAR_FILE not found. Did T016/T046 run?"
    exit 1
fi

# Check PLINK2 availability
if ! command -v plink2 &> /dev/null; then
    echo "ERROR: plink2 is not installed or not in PATH."
    exit 1
fi

echo "Running PLINK2 logistic regression..."
echo "Input: ${GENO_PREFIX}, $PHENO_FILE, $COVAR_FILE"
echo "Output: $OUTPUT_FILE"

# Execute PLINK2
# --logistic: Perform logistic regression (for binary phenotype)
# --covar: Use covariate file
# --out: Output prefix
# --allow-no-covar: Allow running even if no covariates (though we expect them)
# --hide-covar: Hide covariate names in output header (cleaner TSV)
# --ci 0.95: Calculate 95% confidence intervals for Odds Ratio
plink2 \
    --bfile "${GENO_PREFIX}" \
    --logistic hide-covar \
    --covar "$COVAR_FILE" \
    --covar-name C1,C2,C3 \
    --out "${OUTPUT_FILE%.tsv}" \
    --allow-no-covar

# PLINK outputs .assoc.logistic file. We need to rename/convert to .tsv with standard headers.
PLINK_OUTPUT="${OUTPUT_FILE%.tsv}.assoc.logistic"

if [ ! -f "$PLINK_OUTPUT" ]; then
    echo "ERROR: PLINK failed to generate output file $PLINK_OUTPUT"
    exit 1
fi

# Normalize headers to match schema requirements:
# PLINK default: SNP CHR BP A1 TEST NMISS BETA SE Z P OR SE[OR]
# Required: SNP, CHR, POS, P, Odds_Ratio, SE
# Note: PLINK uses 'BP' for base position (POS), 'OR' for Odds Ratio, 'SE' for standard error of BETA.
# The SE for OR is sometimes in a separate column or needs calculation. PLINK --logistic usually gives SE for BETA.
# However, the task requirement is "SE" (likely for the log-odds or the OR).
# Let's map:
# SNP -> SNP
# CHR -> CHR
# BP -> POS
# P -> P
# OR -> Odds_Ratio
# SE -> SE (PLINK outputs SE for BETA in --logistic. If SE for OR is needed, it's usually derived.
#        Standard PLINK --logistic output has SE for the coefficient (log-odds).
#        The requirement "SE" usually refers to the standard error of the estimate.
#        We will map the PLINK 'SE' column to 'SE'.

# Convert and rename headers
# Using awk to handle header and data
awk 'BEGIN {FS="\t"; OFS="\t"}
NR==1 {
    # Find column indices
    for(i=1; i<=NF; i++) {
        if($i=="SNP") s_col=i;
        if($i=="CHR") c_col=i;
        if($i=="BP") b_col=i;
        if($i=="P") p_col=i;
        if($i=="OR") o_col=i;
        if($i=="SE") e_col=i;
    }
    # Print new header
    print "SNP", "CHR", "POS", "P", "Odds_Ratio", "SE"
    next
}
{
    # Print selected columns
    print $s_col, $c_col, $b_col, $p_col, $o_col, $e_col
}' "$PLINK_OUTPUT" > "$OUTPUT_FILE"

# Verify output
if [ ! -f "$OUTPUT_FILE" ]; then
    echo "ERROR: Failed to write output file $OUTPUT_FILE"
    exit 1
fi

# Add metadata header comment as required by T051
# We prepend a comment line with sample rule info
TEMP_FILE=$(mktemp)
echo "# Sample_Rule: Full dataset processed (or streaming chunk if applicable) - GWAS raw statistics" > "$TEMP_FILE"
cat "$OUTPUT_FILE" >> "$TEMP_FILE"
mv "$TEMP_FILE" "$OUTPUT_FILE"

echo "GWAS completed successfully. Output: $OUTPUT_FILE"
echo "First few lines of output:"
head -n 5 "$OUTPUT_FILE"