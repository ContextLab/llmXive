#!/bin/bash
# run_pipeline.sh - Flexible wrapper for the Yeast CRE Analysis Pipeline
#
# Usage:
#   ./run_pipeline.sh [OPTIONS]
#
# Options:
#   --config <path>      Path to a custom manifest.yaml (default: data/manifest.yaml)
#   --output-dir <path>  Directory for all pipeline outputs (default: results)
#   --strict             Enable strict data mode (fatal errors on anomalies)
#   --help               Show this help message
#
# This script orchestrates the pipeline phases in dependency order:
# Phase 2 (Foundation) -> Phase 3 (US1) -> Phase 4 (US2) -> Phase 5 (US3)
#
# It respects the Constitution Principle II: no synthetic fallbacks.
# Any data anomaly in strict mode will abort the pipeline.

set -e  # Exit immediately on error
set -o pipefail

# Default configuration
DEFAULT_MANIFEST="data/manifest.yaml"
DEFAULT_OUTPUT_DIR="results"
LOG_FILE="logs/pipeline.log"
STRICT_MODE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --config)
            MANIFEST_FILE="$2"
            shift 2
            ;;
        --output-dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --strict)
            STRICT_MODE=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --config <path>      Path to a custom manifest.yaml (default: data/manifest.yaml)"
            echo "  --output-dir <path>  Directory for all pipeline outputs (default: results)"
            echo "  --strict             Enable strict data mode (fatal errors on anomalies)"
            echo "  --help               Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Set final paths
MANIFEST_FILE="${MANIFEST_FILE:-$DEFAULT_MANIFEST}"
OUTPUT_DIR="${OUTPUT_DIR:-$DEFAULT_OUTPUT_DIR}"

# Logging setup
log() {
    local level="$1"
    local message="$2"
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    echo "[$timestamp] [$level] $message" | tee -a "$LOG_FILE"
}

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"
log "INFO" "Starting pipeline execution"
log "INFO" "Configuration: Manifest=$MANIFEST_FILE, Output=$OUTPUT_DIR, Strict=$STRICT_MODE"

# Pre-flight checks
if [[ ! -f "$MANIFEST_FILE" ]]; then
    log "ERROR" "Manifest file not found: $MANIFEST_FILE"
    exit 1
fi

# Create output directory structure
mkdir -p "$OUTPUT_DIR"
mkdir -p "data/processed"
mkdir -p "tracks"
mkdir -p "logs"

log "INFO" "Pre-flight checks passed"

# -----------------------------------------------------------------------------
# PHASE 2: Foundational Infrastructure
# -----------------------------------------------------------------------------
log "INFO" "Starting Phase 2: Foundational Infrastructure"

# T005: Download raw data
log "INFO" "Executing T005: Download raw data"
bash code/01_download.sh --config "$MANIFEST_FILE" --output-dir "$OUTPUT_DIR"
if [[ $? -ne 0 ]]; then
    log "ERROR" "T005 failed: Download step aborted"
    exit 1
fi

# T006: Preprocess (trim & align)
log "INFO" "Executing T006: Preprocess data"
bash code/02_preprocess.sh --config "$MANIFEST_FILE" --output-dir "$OUTPUT_DIR"
if [[ $? -ne 0 ]]; then
    log "ERROR" "T006 failed: Preprocessing step aborted"
    exit 1
fi

# T007: Call peaks (MACS2 sweep)
log "INFO" "Executing T007: Call peaks"
bash code/03_call_peaks.sh --config "$MANIFEST_FILE" --output-dir "$OUTPUT_DIR"
if [[ $? -ne 0 ]]; then
    log "ERROR" "T007 failed: Peak calling step aborted"
    exit 1
fi

# T008: Annotate peaks
log "INFO" "Executing T008: Annotate peaks"
python code/03_annotate.py --config "$MANIFEST_FILE" --output-dir "$OUTPUT_DIR"
if [[ $? -ne 0 ]]; then
    log "ERROR" "T008 failed: Annotation step aborted"
    exit 1
fi

# T007c: Extract peak signals
log "INFO" "Executing T007c: Extract peak signals"
Rscript code/03c_extract_peak_signals.R --config "$MANIFEST_FILE" --output-dir "$OUTPUT_DIR"
if [[ $? -ne 0 ]]; then
    log "ERROR" "T007c failed: Peak signal extraction aborted"
    exit 1
fi

# T042: Load Hi-C data
log "INFO" "Executing T042: Load Hi-C data"
bash code/04b_load_hic.sh --config "$MANIFEST_FILE" --output-dir "$OUTPUT_DIR"
if [[ $? -ne 0 ]]; then
    log "ERROR" "T042 failed: Hi-C data loading aborted"
    exit 1
fi

# T009a & T009b: Define null regions and compute signal
log "INFO" "Executing T009a: Define null regions"
bash code/06a_define_null_regions.sh --config "$MANIFEST_FILE" --output-dir "$OUTPUT_DIR"
if [[ $? -ne 0 ]]; then
    log "ERROR" "T009a failed: Null region definition aborted"
    exit 1
fi

log "INFO" "Executing T009b: Compute null signal"
bash code/06b_compute_null_signal.sh --config "$MANIFEST_FILE" --output-dir "$OUTPUT_DIR"
if [[ $? -ne 0 ]]; then
    log "ERROR" "T009b failed: Null signal computation aborted"
    exit 1
fi

# T043: Compute delta peak signal
log "INFO" "Executing T043: Compute delta peak signal"
python code/05b_compute_delta_signal.py --config "$MANIFEST_FILE" --output-dir "$OUTPUT_DIR"
if [[ $? -ne 0 ]]; then
    log "ERROR" "T043 failed: Delta signal computation aborted"
    exit 1
fi

# T051: Validate eQTL schema
log "INFO" "Executing T051: Validate eQTL schema"
python code/01b_validate_eqtl_schema.py --config "$MANIFEST_FILE" --output-dir "$OUTPUT_DIR"
if [[ $? -ne 0 ]]; then
    log "ERROR" "T051 failed: eQTL schema validation aborted"
    exit 1
fi

# T045: Stream eQTL data
log "INFO" "Executing T045: Stream eQTL data"
python code/01_stream_eqtl.py --config "$MANIFEST_FILE" --output-dir "$OUTPUT_DIR"
if [[ $? -ne 0 ]]; then
    log "ERROR" "T045 failed: eQTL streaming aborted"
    exit 1
fi

log "INFO" "Phase 2 completed successfully"

# -----------------------------------------------------------------------------
# PHASE 3: User Story 1 - Generate ranked CRE catalog
# -----------------------------------------------------------------------------
log "INFO" "Starting Phase 3: User Story 1 - Generate ranked CRE catalog"

# T04_filter_impl: Filter and calculate VIF
log "INFO" "Executing T04_filter_impl: Filter and calculate VIF"
python code/04_filter.py --config "$MANIFEST_FILE" --output-dir "$OUTPUT_DIR"
if [[ $? -ne 0 ]]; then
    log "ERROR" "T04_filter_impl failed: Filtering step aborted"
    exit 1
fi

# T05_weights_impl: Compute weights
log "INFO" "Executing T05_weights_impl: Compute weights"
python code/05_weights.py --config "$MANIFEST_FILE" --output-dir "$OUTPUT_DIR"
if [[ $? -ne 0 ]]; then
    log "ERROR" "T05_weights_impl failed: Weight computation aborted"
    exit 1
fi

# T06_lmm_impl: Fit LMM models
log "INFO" "Executing T06_lmm_impl: Fit LMM models"
Rscript code/06_lmm.R --config "$MANIFEST_FILE" --output-dir "$OUTPUT_DIR"
if [[ $? -ne 0 ]]; then
    log "ERROR" "T06_lmm_impl failed: LMM fitting aborted"
    exit 1
fi

# T007_sweep: FDR sweep analysis
log "INFO" "Executing T007_sweep: FDR sweep analysis"
Rscript code/03_sweep_analysis.R --config "$MANIFEST_FILE" --output-dir "$OUTPUT_DIR"
if [[ $? -ne 0 ]]; then
    log "ERROR" "T007_sweep failed: FDR sweep analysis aborted"
    exit 1
fi

# T018: Generate reports
log "INFO" "Executing T018: Generate reports"
Rscript code/10_generate_reports.R --config "$MANIFEST_FILE" --output-dir "$OUTPUT_DIR"
if [[ $? -ne 0 ]]; then
    log "ERROR" "T018 failed: Report generation aborted"
    exit 1
fi

# T027: Add disclaimer
log "INFO" "Executing T027: Add disclaimer"
python code/10_add_disclaimer.py --config "$MANIFEST_FILE" --output-dir "$OUTPUT_DIR"
if [[ $? -ne 0 ]]; then
    log "ERROR" "T027 failed: Disclaimer injection aborted"
    exit 1
fi

log "INFO" "Phase 3 completed successfully"

# -----------------------------------------------------------------------------
# PHASE 4: User Story 2 - Statistical evidence
# -----------------------------------------------------------------------------
log "INFO" "Starting Phase 4: User Story 2 - Statistical evidence"

# T022: Permutation test
log "INFO" "Executing T022: Permutation test"
Rscript code/07_permutation_test.R --config "$MANIFEST_FILE" --output-dir "$OUTPUT_DIR"
if [[ $? -ne 0 ]]; then
    log "ERROR" "T022 failed: Permutation test aborted"
    exit 1
fi

# T049: Permutation checkpoint
log "INFO" "Executing T049: Permutation checkpoint"
Rscript code/07_permutation_checkpoint.R --config "$MANIFEST_FILE" --output-dir "$OUTPUT_DIR"
if [[ $? -ne 0 ]]; then
    log "ERROR" "T049 failed: Permutation checkpoint aborted"
    exit 1
fi

# T07_report_impl: Generate statistical summary
log "INFO" "Executing T07_report_impl: Generate statistical summary"
Rscript code/07_report.R --config "$MANIFEST_FILE" --output-dir "$OUTPUT_DIR"
if [[ $? -ne 0 ]]; then
    log "ERROR" "T07_report_impl failed: Statistical summary generation aborted"
    exit 1
fi

log "INFO" "Phase 4 completed successfully"

# -----------------------------------------------------------------------------
# PHASE 5: User Story 3 - Visualization
# -----------------------------------------------------------------------------
log "INFO" "Starting Phase 5: User Story 3 - Visualization"

# T08_visualize_impl: Generate bigWig tracks
log "INFO" "Executing T08_visualize_impl: Generate bigWig tracks"
python code/08_visualize.py --config "$MANIFEST_FILE" --output-dir "$OUTPUT_DIR"
if [[ $? -ne 0 ]]; then
    log "ERROR" "T08_visualize_impl failed: Visualization generation aborted"
    exit 1
fi

# T05_validate_cre_gating_impl: ATAC-seq validation
log "INFO" "Executing T05_validate_cre_gating_impl: ATAC-seq validation"
python code/05_validate_cre_gating.py --config "$MANIFEST_FILE" --output-dir "$OUTPUT_DIR"
if [[ $? -ne 0 ]]; then
    log "ERROR" "T05_validate_cre_gating_impl failed: ATAC-seq validation aborted"
    exit 1
fi

log "INFO" "Phase 5 completed successfully"

# -----------------------------------------------------------------------------
# Finalization
# -----------------------------------------------------------------------------
log "INFO" "Running final integrity checks"

# T12_generate_manifest_impl: Traceability
log "INFO" "Executing T12_generate_manifest_impl: Generate traceability manifest"
Rscript code/12_generate_manifest.R --config "$MANIFEST_FILE" --output-dir "$OUTPUT_DIR"
if [[ $? -ne 0 ]]; then
    log "ERROR" "T12_generate_manifest_impl failed: Traceability manifest generation aborted"
    exit 1
fi

# T54: Verify integrity (scan logs for synthetic data)
log "INFO" "Executing T054: Verify integrity"
python code/04_filter.py --check-synthetic --config "$MANIFEST_FILE" --output-dir "$OUTPUT_DIR"
if [[ $? -ne 0 ]]; then
    log "ERROR" "T054 failed: Synthetic data detected in logs"
    exit 1
fi

# T56: Final integrity check
log "INFO" "Executing T056: Final integrity check"
bash code/13_final_integrity_check.sh --config "$MANIFEST_FILE" --output-dir "$OUTPUT_DIR"
if [[ $? -ne 0 ]]; then
    log "ERROR" "T056 failed: Final integrity check aborted"
    exit 1
fi

log "INFO" "Pipeline execution completed successfully"
log "INFO" "Outputs available in: $OUTPUT_DIR"

exit 0