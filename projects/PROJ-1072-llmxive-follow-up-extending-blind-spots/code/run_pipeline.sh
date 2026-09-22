#!/bin/bash
#
# llmXive Pipeline Orchestrator
# Executes the Blind-Spots-Bench analysis pipeline in strict dependency order.
#
# Usage: ./code/run_pipeline.sh [stage]
# Stages:
#   1  - User Story 1: Data Acquisition & Filtering
#   2  - Pilot Study: Threshold Validation
#   3  - User Story 2: CoT Generation & Parsing
#   4  - User Story 3: Classification & Statistical Analysis
#   5  - Validation & Reporting
#   all - Run complete pipeline from stage 1 to 5
#
# Exit codes:
#   0 - Success
#   1 - Stage failure or invalid argument
#

set -e  # Exit immediately on error
set -o pipefail

# Project Root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CODE_DIR="${PROJECT_ROOT}/code"
DATA_DIR="${PROJECT_ROOT}/data"
LOG_DIR="${PROJECT_ROOT}/logs"
CONFIG_FILE="${PROJECT_ROOT}/config.yaml"

# Ensure directories exist
mkdir -p "${LOG_DIR}"
mkdir -p "${DATA_DIR}/raw"
mkdir -p "${DATA_DIR}/filtered"
mkdir -p "${DATA_DIR}/traces"
mkdir -p "${DATA_DIR}/results"
mkdir -p "${DATA_DIR}/validation"
mkdir -p "${DATA_DIR}/pilot"

# Logging setup
log() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo "${msg}"
    echo "${msg}" >> "${LOG_DIR}/pipeline_run.log"
}

fail() {
    log "ERROR: $1"
    exit 1
}

run_stage() {
    local stage_name="$1"
    local script_path="$2"

    if [[ ! -f "${script_path}" ]]; then
        fail "Script not found: ${script_path}"
    fi

    log "=== Starting Stage: ${stage_name} ==="
    log "Executing: ${script_path}"

    # Run the script with Python, ensuring the project root is in the path
    cd "${PROJECT_ROOT}"
    python "${script_path}"
    local exit_code=$?

    if [[ ${exit_code} -ne 0 ]]; then
        fail "Stage '${stage_name}' failed with exit code ${exit_code}"
    fi

    log "=== Stage '${stage_name}' completed successfully ==="
}

# Main execution logic
main() {
    local target_stage="${1:-all}"

    log "Starting llmXive Pipeline Orchestrator"
    log "Target Stage: ${target_stage}"
    log "Project Root: ${PROJECT_ROOT}"

    # Check for config file
    if [[ ! -f "${CONFIG_FILE}" ]]; then
        fail "Configuration file not found: ${CONFIG_FILE}"
    fi

    case "${target_stage}" in
        1)
            run_stage "US1: Data Acquisition & Filtering" "${CODE_DIR}/01_download_and_filter.py"
            ;;
        2)
            run_stage "Pilot: Threshold Validation" "${CODE_DIR}/pilot_study.py"
            run_stage "Pilot: Threshold Validation (Check)" "${CODE_DIR}/validate_pilot.py"
            run_stage "Pilot: Threshold Tuning" "${CODE_DIR}/tune_threshold.py"
            ;;
        3)
            run_stage "US2: CoT Generation" "${CODE_DIR}/02_generate_cot.py"
            run_stage "US2: Parsing & Classification" "${CODE_DIR}/03_parse_and_classify.py"
            ;;
        4)
            run_stage "US3: Statistical Analysis" "${CODE_DIR}/04_statistical_analysis.py"
            run_stage "US3: Human Label Ingestion" "${CODE_DIR}/ingest_human_labels.py"
            run_stage "US3: Classifier Validation" "${CODE_DIR}/validate_classifier.py"
            ;;
        5)
            run_stage "Polish: Paper Sections" "${CODE_DIR}/generate_paper_sections.py"
            run_stage "Polish: State Update" "${CODE_DIR}/update_state.py"
            run_stage "Polish: Consistency Check" "${CODE_DIR}/06_consistency_check.py"
            ;;
        all)
            log "Running full pipeline..."
            run_stage "US1: Data Acquisition & Filtering" "${CODE_DIR}/01_download_and_filter.py"
            run_stage "Pilot: Threshold Validation" "${CODE_DIR}/pilot_study.py"
            run_stage "Pilot: Threshold Validation (Check)" "${CODE_DIR}/validate_pilot.py"
            run_stage "Pilot: Threshold Tuning" "${CODE_DIR}/tune_threshold.py"
            run_stage "US2: CoT Generation" "${CODE_DIR}/02_generate_cot.py"
            run_stage "US2: Parsing & Classification" "${CODE_DIR}/03_parse_and_classify.py"
            run_stage "US3: Statistical Analysis" "${CODE_DIR}/04_statistical_analysis.py"
            run_stage "US3: Human Label Ingestion" "${CODE_DIR}/ingest_human_labels.py"
            run_stage "US3: Classifier Validation" "${CODE_DIR}/validate_classifier.py"
            run_stage "Polish: Paper Sections" "${CODE_DIR}/generate_paper_sections.py"
            run_stage "Polish: State Update" "${CODE_DIR}/update_state.py"
            run_stage "Polish: Consistency Check" "${CODE_DIR}/06_consistency_check.py"
            ;;
        *)
            fail "Invalid stage: ${target_stage}. Use 1, 2, 3, 4, 5, or all."
            ;;
    esac

    log "Pipeline execution finished successfully."
}

main "$@"
