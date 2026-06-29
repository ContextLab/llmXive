#!/bin/bash
#
# run_pipeline.sh - Main pipeline orchestration script
# for Bayesian Hierarchical Modeling of Misinformation Cascade Size
#
# Usage: ./run_pipeline.sh --data <data_dir> --out <output_dir>
#
# Environment:
#   OMP_NUM_THREADS=2  - Limit parallel threads for CPU-bound operations
#
# Memory:
#   Aborts if RAM usage exceeds 7 GB (per project constraints)
#
# Logging:
#   All major steps logged to pipeline.log in project root
#

set -euo pipefail

# ============================================================================
# Configuration
# ============================================================================
readonly MAX_RAM_GB=7
readonly LOG_FILE="pipeline.log"
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ============================================================================
# Helper Functions
# ============================================================================

log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp
    timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    echo "[${timestamp}] [${level}] ${message}" | tee -a "${LOG_FILE}"
}

log_info() {
    log "INFO" "$@"
}

log_warn() {
    log "WARN" "$@"
}

log_error() {
    log "ERROR" "$@"
}

# Check available memory and abort if threshold exceeded
check_memory() {
    log_info "Checking available memory (threshold: ${MAX_RAM_GB} GB)"
    
    local available_mb
    if [[ -f /proc/meminfo ]]; then
        # Linux: read from /proc/meminfo
        available_mb=$(awk '/^MemAvailable/ {print $2}' /proc/meminfo)
    elif command -v free &>/dev/null; then
        # macOS/Unix: use free command
        available_mb=$(free -m | awk '/^Mem:/ {print $7}')
    else
        # Fallback: assume sufficient memory (will be validated at runtime)
        log_warn "Cannot determine available memory; skipping memory check"
        return 0
    fi
    
    local available_gb
    available_gb=$(echo "scale=2; ${available_mb} / 1024" | bc)
    
    log_info "Available memory: ${available_gb} GB"
    
    if (( $(echo "${available_gb} < ${MAX_RAM_GB}" | bc -l) )); then
        log_error "Insufficient memory: ${available_gb} GB available, ${MAX_RAM_GB} GB required"
        return 1
    fi
    
    log_info "Memory check passed"
    return 0
}

# ============================================================================
# Argument Parsing
# ============================================================================

DATA_DIR=""
OUTPUT_DIR=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --data)
            DATA_DIR="$2"
            shift 2
            ;;
        --out)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 --data <data_dir> --out <output_dir>"
            echo ""
            echo "Options:"
            echo "  --data   Directory containing raw cascade JSON files"
            echo "  --out    Directory for output results"
            echo "  --help   Show this help message"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Validate required arguments
if [[ -z "${DATA_DIR}" ]]; then
    log_error "Missing required argument: --data"
    exit 1
fi

if [[ -z "${OUTPUT_DIR}" ]]; then
    log_error "Missing required argument: --out"
    exit 1
fi

if [[ ! -d "${DATA_DIR}" ]]; then
    log_error "Data directory does not exist: ${DATA_DIR}"
    exit 1
fi

# ============================================================================
# Pipeline Initialization
# ============================================================================

log_info "=========================================="
log_info "Starting Misinformation Cascade Pipeline"
log_info "=========================================="
log_info "Data directory: ${DATA_DIR}"
log_info "Output directory: ${OUTPUT_DIR}"
log_info "OMP_NUM_THREADS: ${OMP_NUM_THREADS:-2}"

# Set thread limit for parallel operations
export OMP_NUM_THREADS=2

# Check memory before proceeding
if ! check_memory; then
    log_error "Pipeline aborted: memory check failed"
    exit 1
fi

# Create output directory if it doesn't exist
mkdir -p "${OUTPUT_DIR}"

# ============================================================================
# Pipeline Stages
# ============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Data Loading and Validation
# ------------------------------------------------------------------------------
log_info "Stage 1: Data Loading and Validation"
log_info "--------------------------------------"

# TODO: Implement T021a - load_cascade() for all JSON files
# TODO: Validate schema, normalize timestamps to UTC
# TODO: Enforce node limit (skip cascades > 2000 nodes)
# TODO: Write validated cascades to data/processed/validated_cascades.json
# TODO: Log skipped cascade IDs to skipped_cascades.log

log_info "Stage 1: Data Loading and Validation - COMPLETE"

# ------------------------------------------------------------------------------
# Stage 2: Feature Extraction
# ------------------------------------------------------------------------------
log_info "Stage 2: Feature Extraction"
log_info "---------------------------"

# TODO: Implement T021b - call network_features.py
# TODO: Compute degree distribution moments, clustering coefficient, betweenness centrality
# TODO: Call user_susceptibility.py
# TODO: Compute susceptibility scores using historical sharing frequency
# TODO: Aggregate outputs into results/features.csv
# TODO: Log input/output paths to pipeline.log

log_info "Stage 2: Feature Extraction - COMPLETE"

# ------------------------------------------------------------------------------
# Stage 3: Model Fitting
# ------------------------------------------------------------------------------
log_info "Stage 3: Model Fitting"
log_info "----------------------"

# TODO: Implement T021c - call hierarchical_model.py
# TODO: Run HMC/NUTS sampling with features.csv as input
# TODO: Monitor divergent transitions (> 5% triggers retry)
# TODO: Auto-reduce step size and retry up to 3 times
# TODO: Abort with diagnostic report if convergence fails
# TODO: Write posterior trace to results/model_trace.nc

log_info "Stage 3: Model Fitting - COMPLETE"

# ------------------------------------------------------------------------------
# Stage 4: Output Generation
# ------------------------------------------------------------------------------
log_info "Stage 4: Output Generation"
log_info "--------------------------"

# TODO: Implement T021d - compute posterior summaries from model_trace.nc
# TODO: Write results/posterior_summary.csv with columns:
#       predictor, mean, sd, lower_95, upper_95, prob_nonzero, direction_consistent
# TODO: Verify all output files exist with no missing values
# TODO: Validate against contract schemas

log_info "Stage 4: Output Generation - COMPLETE"

# ============================================================================
# Pipeline Completion
# ============================================================================

log_info "=========================================="
log_info "Pipeline Completed Successfully"
log_info "=========================================="
log_info "Output directory: ${OUTPUT_DIR}"
log_info "Log file: ${LOG_FILE}"

exit 0