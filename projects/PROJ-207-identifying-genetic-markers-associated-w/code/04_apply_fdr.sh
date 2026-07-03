#!/usr/bin/env bash
# 04_apply_fdr.sh: Apply Benjamini-Hochberg FDR correction to GWAS results
#
# Usage:
#   ./04_apply_fdr.sh <input_gwas_tsv> <output_fdr_tsv>
#
# Inputs:
#   <input_gwas_tsv> : Path to raw GWAS output (e.g., data/interim/gwas_raw.tsv)
#   <output_fdr_tsv> : Path for final FDR-corrected output
#
# Outputs:
#   <output_fdr_tsv> : TSV with q-values, significant flags, and disclaimer
#
# Requirements:
#   - Python 3.11+ with pandas, numpy
#   - code/utils/fdr_correction.py must exist

set -euo pipefail

# --- Configuration ---
readonly SCRIPT_NAME=$(basename "$0")
readonly FDR_SCRIPT="code/utils/fdr_correction.py"
readonly DISCLAIMER_TEXT="Findings are associational, not causal. Results indicate statistical associations only and do not imply causation."

# --- Functions ---
log_info() {
    echo "[INFO] $(date '+%Y-%m-%d %H:%M:%S') - $*" >&2
}

log_error() {
    echo "[ERROR] $(date '+%Y-%m-%d %H:%M:%S') - $*" >&2
}

check_prereqs() {
    if [[ ! -f "$FDR_SCRIPT" ]]; then
        log_error "FDR correction script not found: $FDR_SCRIPT"
        exit 1
    fi

    if ! command -v python3 &> /dev/null; then
        log_error "Python3 not found in PATH."
        exit 1
    fi
}

validate_inputs() {
    local input_file="$1"
    local output_file="$2"

    if [[ -z "$input_file" || -z "$output_file" ]]; then
        log_error "Missing required arguments."
        echo "Usage: $SCRIPT_NAME <input_gwas_tsv> <output_fdr_tsv>"
        exit 1
    fi

    if [[ ! -f "$input_file" ]]; then
        log_error "Input GWAS file not found: $input_file"
        exit 1
    fi
}

run_fdr_correction() {
    local input_file="$1"
    local output_file="$2"

    log_info "Applying Benjamini-Hochberg FDR correction..."
    log_info "Input: $input_file"
    log_info "Output: $output_file"

    # Execute Python script
    # The script handles:
    # 1. Loading the TSV
    # 2. Calculating q-values
    # 3. Flagging significant SNPs (q < 0.05)
    # 4. Prepending the mandatory disclaimer to the header
    # 5. Writing the final file
    python3 "$FDR_SCRIPT" \
        --input "$input_file" \
        --output "$output_file"

    if [[ ! -f "$output_file" ]]; then
        log_error "FDR correction failed: Output file not created."
        exit 2
    fi

    log_info "FDR correction complete."
    log_info "Significant SNPs (q < 0.05) are flagged in the output."
    log_info "Mandatory disclaimer has been prepended to the file header."
}

# --- Main ---
main() {
    local input_file="${1:-}"
    local output_file="${2:-}"

    check_prereqs
    validate_inputs "$input_file" "$output_file"

    run_fdr_correction "$input_file" "$output_file"

    log_info "Pipeline completed successfully."
}

main "$@"