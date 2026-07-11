#!/bin/bash
#
# run_ariba.sh - Wrapper script to identify antibiotic resistance genes using ARIba
#
# This script executes ARIba to screen assembled contigs or genomes against the
# CARD (Comprehensive Antibiotic Resistance Database) reference database.
#
# Usage:
#   ./run_ariba.sh <input_contigs.fasta> <output_directory> [card_db_path]
#
# Arguments:
#   input_contigs.fasta  - Path to the input FASTA file containing assembled contigs
#   output_directory     - Directory where ARIba results will be written
#   card_db_path         - (Optional) Path to the CARD database directory.
#                          If not provided, defaults to data/raw/card_db/
#
# Environment Variables:
#   ARIBA_DB_PATH - Alternative way to specify CARD database path
#   ARIBA_THREADS - Number of threads to use (default: 4)
#
# Outputs:
#   Creates the following files in output_directory:
#     - ariba_report.csv      - Summary of resistance genes found
#     - ariba_report.tsv      - Tab-separated version of the report
#     - ariba_report.txt      - Human-readable report
#     - genes.fa              - Sequences of identified resistance genes
#     - genes_proteins.fa     - Protein sequences of identified genes
#     - ariba_report.csv.gz   - Compressed CSV report
#
# Exit Codes:
#   0 - Success
#   1 - Missing input file
#   2 - ARIba execution failed
#   3 - Invalid arguments
#

set -euo pipefail

# --- Configuration ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DEFAULT_CARD_DB="${PROJECT_ROOT}/data/raw/card_db"
DEFAULT_THREADS=4

# --- Logging Setup ---
log_info() {
    echo "[INFO] $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo "[ERROR] $(date '+%Y-%m-%d %H:%M:%S') - $1" >&2
}

# --- Argument Parsing ---
if [[ $# -lt 2 ]]; then
    log_error "Usage: $0 <input_contigs.fasta> <output_directory> [card_db_path]"
    exit 3
fi

INPUT_FASTA="$1"
OUTPUT_DIR="$2"
CARD_DB="${3:-${ARIBA_DB_PATH:-$DEFAULT_CARD_DB}}"
THREADS="${ARIBA_THREADS:-$DEFAULT_THREADS}"

# --- Validation ---
if [[ ! -f "$INPUT_FASTA" ]]; then
    log_error "Input FASTA file not found: $INPUT_FASTA"
    exit 1
fi

if [[ ! -d "$CARD_DB" ]]; then
    log_error "CARD database directory not found: $CARD_DB"
    log_error "Please ensure the database is downloaded to this location or set ARIBA_DB_PATH."
    exit 1
fi

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

log_info "Starting ARIba analysis..."
log_info "Input: $INPUT_FASTA"
log_info "Output: $OUTPUT_DIR"
log_info "Database: $CARD_DB"
log_info "Threads: $THREADS"

# --- Run ARIba ---
# ARIba command structure:
# ariba run <db> <input.fasta> <outdir> [options]
#
# Key options:
#   -threads <int> : Number of threads
#   -minid <float> : Minimum identity (default 0.9)
#   -mincov <float> : Minimum coverage (default 0.9)
#   -report_type csv : Generate CSV report
#
log_info "Executing ARIba..."

if command -v ariba &> /dev/null; then
    ariba run \
        -threads "$THREADS" \
        -minid 0.9 \
        -mincov 0.9 \
        "$CARD_DB" \
        "$INPUT_FASTA" \
        "$OUTPUT_DIR/ariba_temp" \
        --report_type csv
else
    log_error "ARIba executable not found. Please ensure 'ariba' is in your PATH."
    log_error "Install via: conda install -c bioconda ariba"
    exit 2
fi

# --- Post-Processing ---
# Move the generated report to the final output directory with a clean name
if [[ -f "$OUTPUT_DIR/ariba_temp/ariba_report.csv" ]]; then
    mv "$OUTPUT_DIR/ariba_temp/ariba_report.csv" "$OUTPUT_DIR/ariba_report.csv"
    mv "$OUTPUT_DIR/ariba_temp/ariba_report.tsv" "$OUTPUT_DIR/ariba_report.tsv" 2>/dev/null || true
    mv "$OUTPUT_DIR/ariba_temp/ariba_report.txt" "$OUTPUT_DIR/ariba_report.txt" 2>/dev/null || true
    mv "$OUTPUT_DIR/ariba_temp/genes.fa" "$OUTPUT_DIR/genes.fa" 2>/dev/null || true
    mv "$OUTPUT_DIR/ariba_temp/genes_proteins.fa" "$OUTPUT_DIR/genes_proteins.fa" 2>/dev/null || true
    
    # Compress the CSV for storage efficiency
    gzip -f "$OUTPUT_DIR/ariba_report.csv"
    
    log_info "ARIba analysis completed successfully."
    log_info "Results written to: $OUTPUT_DIR"
else
    log_error "ARIba report was not generated. Check the ariba_temp directory for errors."
    exit 2
fi

# --- Cleanup ---
rm -rf "$OUTPUT_DIR/ariba_temp"
log_info "Temporary files cleaned up."

exit 0
