#!/usr/bin/env bash
# 03_gwas.sh: Execute PLINK logistic regression for GWAS
#
# Usage:
#   ./03_gwas.sh <plink_prefix> <pheno_file> <covar_file> <output_prefix>
#
# Inputs:
#   <plink_prefix> : Prefix for PLINK binary files (.bed, .bim, .fam)
#   <pheno_file>   : Path to phenotype file (format: FID IID PHENO)
#   <covar_file>   : Path to covariate file (format: FID IID COV1 COV2 ...)
#   <output_prefix>: Prefix for output files
#
# Outputs:
#   <output_prefix>.assoc.logistic : Raw association statistics
#
# Requirements:
#   - plink (v1.9 or v2.0) must be in PATH
#
# Note:
#   - FDR correction is NOT applied here (handled by T022).
#   - This script outputs raw p-values and statistics.

set -euo pipefail

# --- Configuration ---
readonly SCRIPT_NAME=$(basename "$0")
readonly PLINK_CMD="plink"

# --- Functions ---
log_info() {
    echo "[INFO] $(date '+%Y-%m-%d %H:%M:%S') - $*" >&2
}

log_error() {
    echo "[ERROR] $(date '+%Y-%m-%d %H:%M:%S') - $*" >&2
}

check_prereqs() {
    if ! command -v "$PLINK_CMD" &> /dev/null; then
        log_error "PLINK not found in PATH. Please install PLINK."
        exit 1
    fi
}

validate_inputs() {
    local plink_prefix="$1"
    local pheno_file="$2"
    local covar_file="$3"

    if [[ -z "$plink_prefix" || -z "$pheno_file" || -z "$covar_file" ]]; then
        log_error "Missing required arguments."
        echo "Usage: $SCRIPT_NAME <plink_prefix> <pheno_file> <covar_file> <output_prefix>"
        exit 1
    fi

    if [[ ! -f "${plink_prefix}.bed" ]]; then
        log_error "PLINK binary file not found: ${plink_prefix}.bed"
        exit 1
    fi

    if [[ ! -f "${plink_prefix}.bim" ]]; then
        log_error "PLINK bim file not found: ${plink_prefix}.bim"
        exit 1
    fi

    if [[ ! -f "${plink_prefix}.fam" ]]; then
        log_error "PLINK fam file not found: ${plink_prefix}.fam"
        exit 1
    fi

    if [[ ! -f "$pheno_file" ]]; then
        log_error "Phenotype file not found: $pheno_file"
        exit 1
    fi

    if [[ ! -f "$covar_file" ]]; then
        log_error "Covariate file not found: $covar_file"
        exit 1
    fi
}

run_gwas() {
    local plink_prefix="$1"
    local pheno_file="$2"
    local covar_file="$3"
    local output_prefix="$4"
    local output_file="${output_prefix}.assoc.logistic"

    log_info "Starting GWAS with PLINK logistic regression..."

    # Execute PLINK
    # --logistic: Perform logistic regression
    # --covar: Use covariates
    # --pheno: Use phenotype file
    # --out: Output prefix
    # --threads: Use multiple threads if available
    $PLINK_CMD \
        --bfile "$plink_prefix" \
        --logistic \
        --covar "$covar_file" \
        --pheno "$pheno_file" \
        --out "$output_prefix" \
        --threads 4

    if [[ ! -f "$output_file" ]]; then
        log_error "GWAS failed: Output file not created."
        exit 2
    fi

    log_info "GWAS complete. Output: $output_file"
}

# --- Main ---
main() {
    local plink_prefix="${1:-}"
    local pheno_file="${2:-}"
    local covar_file="${3:-}"
    local output_prefix="${4:-}"

    check_prereqs
    validate_inputs "$plink_prefix" "$pheno_file" "$covar_file"

    run_gwas "$plink_prefix" "$pheno_file" "$covar_file" "$output_prefix"

    log_info "Pipeline completed successfully."
}

main "$@"
