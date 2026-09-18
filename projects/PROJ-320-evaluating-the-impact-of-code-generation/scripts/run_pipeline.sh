#!/bin/bash
#
# Full research pipeline execution script
#
# This script runs the complete llm-code-review-impact analysis pipeline
# from data fetching to final report generation.
#
# Usage: ./scripts/run_pipeline.sh
#
# Exit codes:
#   0 - All stages completed successfully
#   1 - One or more stages failed
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check Python version
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed"
        exit 1
    fi

    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    if [[ $(echo "$PYTHON_VERSION < 3.11" | bc -l) -eq 1 ]]; then
        log_error "Python 3.11 or higher is required (found $PYTHON_VERSION)"
        exit 1
    fi
    log_info "Python version: $PYTHON_VERSION"

    # Check GitHub token
    if [ -z "$GITHUB_TOKEN" ]; then
        log_error "GITHUB_TOKEN environment variable is not set"
        exit 1
    fi
    log_info "GitHub token: configured"

    # Check dependencies
    if ! python3 -c "import requests, pandas, scipy" &> /dev/null; then
        log_error "Dependencies not installed. Run: pip install -r requirements.txt"
        exit 1
    fi
    log_info "Dependencies: installed"
}

# Create necessary directories
setup_directories() {
    log_info "Setting up directories..."
    python3 code/setup_directories.py
}

# Run a single pipeline stage
run_stage() {
    local stage_name="$1"
    local script="$2"

    log_info "=========================================="
    log_info "Stage: $stage_name"
    log_info "Script: $script"
    log_info "=========================================="

    if ! python3 "$script"; then
        log_error "Stage '$stage_name' failed!"
        exit 1
    fi

    log_info "Stage '$stage_name' completed successfully"
    echo ""
}

# Main pipeline execution
main() {
    log_info "Starting llm-code-review-impact pipeline"
    log_info "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""

    # Prerequisites
    check_prerequisites
    setup_directories

    # Stage 1: Data Collection
    run_stage "Fetch GitHub Data" "code/data/fetch_github.py"

    # Stage 2: Classification
    run_stage "Classify PRs" "code/data/classify_prs.py"

    # Stage 3: Save Labeled Dataset
    run_stage "Save Labeled Dataset" "code/data/save_labeled_dataset.py"

    # Stage 4: Complexity Analysis
    run_stage "Compute Complexity Scores" "code/analysis/save_complexity_scores.py"

    # Stage 5: Metrics Extraction
    run_stage "Extract Review Metrics" "code/data/extract_metrics.py"

    # Stage 6: Statistical Tests
    run_stage "Run Statistical Tests" "code/analysis/statistical_tests.py"

    # Stage 7: Results Report
    run_stage "Generate Results Report" "code/analysis/generate_results_report.py"

    # Stage 8: Manual Audit
    run_stage "Run Manual Validation Audit" "code/audit/manual_validation.py"

    # Stage 9: Visualizations
    run_stage "Generate Visualizations" "code/analysis/visualizations.py"

    # Stage 10: Final Report
    run_stage "Generate Final Report" "code/analysis/generate_final_report.py"

    # Pipeline complete
    log_info "=========================================="
    log_info "Pipeline completed successfully!"
    log_info "=========================================="
    log_info "Output artifacts:"
    log_info "  - data/processed/prs_labeled.csv"
    log_info "  - data/processed/complexity_scores.csv"
    log_info "  - data/processed/prs_metrics.csv"
    log_info "  - data/processed/results.json"
    log_info "  - data/audit/error_rate.json"
    log_info "  - data/processed/gate_status.json"
    log_info "  - reports/figures/boxplots.pdf"
    log_info "  - reports/figures/histograms.pdf"
    log_info "  - reports/figures/correlations.pdf"
    log_info "  - reports/final_report.pdf"
    log_info ""
    log_info "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
}

# Run main function
main "$@"