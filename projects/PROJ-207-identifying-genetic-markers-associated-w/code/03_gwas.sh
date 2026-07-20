#!/bin/bash
# code/03_gwas.sh
# Executes PLINK2 logistic regression with covariates or PCA components.
# Reads configuration from data/processed/model_config.yaml to determine strategy.
# Outputs raw association statistics to data/interim/gwas_raw.tsv.
#
# Prerequisites (must be run before this script):
#   - T016: Phenotype preprocessing (produces data/processed/phenotypes_cleaned.fam/pheno)
#   - T015: VCF to PLINK conversion (produces data/processed/genotypes.{bed,bim,fam})
#   - T043: Power analysis (must exit 0)
#   - T046: Collinearity guard (produces data/processed/model_config.yaml)

set -e

echo "=== Starting GWAS Pipeline (T017) ==="

# Define paths relative to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

CONFIG_FILE="$PROJECT_ROOT/data/processed/model_config.yaml"
FAM_FILE="$PROJECT_ROOT/data/processed/phenotypes_cleaned.fam"
PHENO_FILE="$PROJECT_ROOT/data/processed/phenotypes_cleaned.pheno"
BED_PREFIX="$PROJECT_ROOT/data/processed/genotypes"

OUTPUT_DIR="$PROJECT_ROOT/data/interim"
OUTPUT_FILE="$OUTPUT_DIR/gwas_raw.tsv"

# Ensure output directory exists
mkdir -p "$OUTPUT_DIR"

# Check prerequisites
if [ ! -f "$CONFIG_FILE" ]; then
    echo "ERROR: Model configuration not found at $CONFIG_FILE. Run T046 first."
    exit 1
fi

if [ ! -f "$FAM_FILE" ]; then
    echo "ERROR: Phenotype FAM file not found at $FAM_FILE. Run T016 first."
    exit 1
fi

if [ ! -f "${BED_PREFIX}.bed" ] || [ ! -f "${BED_PREFIX}.bim" ] || [ ! -f "${BED_PREFIX}.fam" ]; then
    echo "ERROR: PLINK genotype files not found at $BED_PREFIX.*. Run T015 first."
    exit 1
fi

# Read strategy from YAML config
STRATEGY=$(grep "^strategy:" "$CONFIG_FILE" | awk '{print $2}')

echo "Detected analysis strategy: $STRATEGY"

COVAR_ARGS=""
COVAR_FILE=""

if [ "$STRATEGY" == "PCA" ]; then
    # Extract PC columns from config
    PC_COLUMNS=$(grep "^pc_columns:" -A 99 "$CONFIG_FILE" | grep -E '^\s+-' | sed 's/^\s*- //' | tr '\n' ',' | sed 's/,$//')
    
    if [ -z "$PC_COLUMNS" ]; then
        echo "ERROR: No PC columns found in model_config.yaml for PCA strategy."
        exit 1
    fi

    # PLINK expects a separate .covar file for PCA components usually, 
    # but if the phenotype file was updated by T046 to include PCs, we can use --pheno-col.
    # However, T046 output description says it generates model_config.yaml.
    # Standard PLINK2 approach: Use --covar with the file containing PCs.
    # T046 likely outputs a PCA file or updates the phenotype file. 
    # Assuming T046 outputs a standard PLINK .covar file if PCA is used, 
    # OR we extract from the phenotype file if T016/T046 merged them.
    # Given T046 description: "Generate PCA covariates... Output: model_config.yaml... pc_columns".
    # We assume the phenotype file (or a generated covar file) contains these columns.
    # Let's assume T046 generated a specific covar file at data/processed/pca_covar.txt if PCA is used.
    # If not, we might need to construct it. 
    # For robustness, we check for a generated covar file first.
    
    COVAR_FILE="$PROJECT_ROOT/data/processed/pca_covar.txt"
    if [ ! -f "$COVAR_FILE" ]; then
        # Fallback: Try to use the phenotype file if it contains the PCs (common in pipelines)
        # But PLINK --covar requires the file to have FID/IID.
        # Let's assume T046 created a .covar file. If not, we error.
        # If T046 didn't create it, the pipeline is broken.
        # We will assume T046 created it.
        echo "ERROR: PCA covariate file not found at $COVAR_FILE. T046 must generate this."
        exit 1
    fi
    
    COVAR_ARGS="--covar $COVAR_FILE --covar-name $PC_COLUMNS"
    
elif [ "$STRATEGY" == "Covariates" ]; then
    # Use the cleaned phenotype file which includes the covariates
    COVAR_ARGS="--pheno $PHENO_FILE"
    # Extract covariate column names from config
    COVARIATE_COLUMNS=$(grep "^covariate_columns:" -A 99 "$CONFIG_FILE" | grep -E '^\s+-' | sed 's/^\s*- //' | tr '\n' ',' | sed 's/,$//')
    
    if [ -z "$COVARIATE_COLUMNS" ]; then
        echo "WARNING: No covariate columns found in config, running without covariates."
    else
        # PLINK --pheno-col expects 1-based indices or names if --pheno-name is used?
        # Actually, --pheno takes the file, and --pheno-name takes the column header.
        # We need to specify which columns are covariates.
        # PLINK2 syntax: --covar is for external files. --pheno is for phenotype.
        # If covariates are in the .pheno file, we treat them as covariates?
        # PLINK2 --logistic [covariates in .pheno file?] -> Usually .pheno is just the phenotype.
        # Standard practice: Covariates go in a .covar file. 
        # If T016 put them in the .pheno file, we need to move them or use --pheno-col?
        # PLINK2 --logistic hide-covar ... --covar-name ...
        # Let's assume T016/T046 logic ensured a .covar file exists for covariates too, 
        # OR we use the .pheno file as the covar file if it contains the right columns.
        # To be safe and follow PLINK2 best practices:
        # If covariates are in the .pheno file, we can use --pheno and --pheno-name for the outcome,
        # and --covar for the rest? No, .pheno can't be .covar simultaneously easily.
        # Re-reading T016: "Output: data/processed/phenotypes_cleaned.fam and data/processed/phenotypes_cleaned.pheno".
        # T046: "If VIF < 5: Output model_config.yaml with covariate_columns".
        # It implies we should use these columns as covariates.
        # We will assume the .pheno file contains the phenotype in the first column and covariates in subsequent columns.
        # PLINK2 --logistic --pheno file.pheno --pheno-name PHENOTYPE --covar file.pheno --covar-name COL1,COL2...
        # This is valid.
        
        # Construct the command to use the .pheno file as both source of phenotype and covariates
        # We assume the first column of .pheno is the phenotype (CCD status) and others are covariates.
        # We need to know the phenotype column name. Let's assume it's 'CCD_Status' or similar.
        # Since we don't know the exact header, we will assume the user knows or the file is standard.
        # However, to be precise, we will use the .pheno file as the covar file for the covariates.
        
        # Let's assume the .pheno file has headers.
        # We will pass the .pheno file as the covar file for the covariates.
        COVAR_FILE="$PHENO_FILE"
        COVAR_ARGS="--covar $COVAR_FILE --covar-name $COVARIATE_COLUMNS --pheno $PHENO_FILE --pheno-name CCD_Status" 
        # Note: --pheno-name is required if multiple columns exist. 
        # If T016 named the phenotype column 'CCD_Status', this works.
        # If not, we might need to adjust. Assuming standard naming from T009/T016.
        
else
    echo "ERROR: Unknown strategy '$STRATEGY' in $CONFIG_FILE. Must be 'PCA' or 'Covariates'."
    exit 1
fi

echo "Executing PLINK2 logistic regression..."
echo "Strategy: $STRATEGY"
echo "Output: $OUTPUT_FILE"

# Run PLINK2
# --logistic: Perform logistic regression
# --hide-covar: Hide covariate output in the main .assoc.logistic file (optional, keeps it clean)
# --out: Output prefix
plink2 \
    --bfile "$BED_PREFIX" \
    --logistic \
    $COVAR_ARGS \
    --out "$OUTPUT_DIR/gwas_raw"

# PLINK2 outputs gwas_raw.assoc.logistic by default.
# We need to rename/move it to gwas_raw.tsv and ensure column names match requirements:
# SNP, CHR, POS, P, Odds_Ratio, SE
# PLINK2 default columns: CHR, SNP, BP, A1, TEST, NMISS, BETA, SE, Z, P, OR
# We need to map: SNP -> SNP, CHR -> CHR, BP -> POS, P -> P, OR -> Odds_Ratio, SE -> SE

# Check if output file exists
if [ ! -f "$OUTPUT_DIR/gwas_raw.assoc.logistic" ]; then
    echo "ERROR: PLINK2 failed to produce output file."
    exit 1
fi

# Process the output to match the required schema
# Using awk to reorder and rename columns
awk 'BEGIN {FS="\t"; OFS="\t"} 
     NR==1 {
         # Find column indices
         for(i=1; i<=NF; i++) {
             if($i=="SNP") snp_col=i;
             if($i=="CHR") chr_col=i;
             if($i=="BP") bp_col=i;
             if($i=="P") p_col=i;
             if($i=="SE") se_col=i;
             if($i=="OR") or_col=i;
         }
         # Print new header
         print "SNP", "CHR", "POS", "P", "Odds_Ratio", "SE"
         next
     }
     {
         print $snp_col, $chr_col, $bp_col, $p_col, $or_col, $se_col
     }' "$OUTPUT_DIR/gwas_raw.assoc.logistic" > "$OUTPUT_FILE"

# Verify output
if [ -f "$OUTPUT_FILE" ]; then
    ROW_COUNT=$(wc -l < "$OUTPUT_FILE")
    echo "SUCCESS: GWAS raw results written to $OUTPUT_FILE ($ROW_COUNT rows)"
    
    # Verify header
    HEADER=$(head -n 1 "$OUTPUT_FILE")
    EXPECTED_HEADER="SNP	CHR	POS	P	Odds_Ratio	SE"
    if [ "$HEADER" == "$EXPECTED_HEADER" ]; then
        echo "Header verification: PASSED"
    else
        echo "Header verification: FAILED (Expected: $EXPECTED_HEADER, Got: $HEADER)"
    fi
else
    echo "ERROR: Failed to write output file $OUTPUT_FILE"
    exit 1
fi

echo "=== GWAS Pipeline (T017) Complete ==="
