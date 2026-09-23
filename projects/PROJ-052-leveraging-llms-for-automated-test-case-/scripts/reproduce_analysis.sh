#!/bin/bash
# Reproducibility Script for PROJ-052
# This script sets the random seed, runs the pipeline on the same sample set,
# and verifies that the analysis_results.json hash matches the original.

set -e

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_DIR="${PROJECT_ROOT}/data"
STATE_DIR="${PROJECT_ROOT}/state/projects"
RESULTS_FILE="${DATA_DIR}/analysis_results.json"
CHECKSUM_FILE="${STATE_DIR}/PROJ-052-leveraging-llms-for-automated-test-case-.yaml"
LOG_FILE="${DATA_DIR}/reproduce_run.log"

echo "=== Reproducibility Check Started ===" | tee "${LOG_FILE}"
echo "Project Root: ${PROJECT_ROOT}" | tee -a "${LOG_FILE}"
echo "Date: $(date)" | tee -a "${LOG_FILE}"

# 1. Verify Prerequisites
if [ ! -f "${RESULTS_FILE}" ]; then
    echo "ERROR: Original results file not found at ${RESULTS_FILE}" | tee -a "${LOG_FILE}"
    exit 1
fi

if [ ! -f "${CHECKSUM_FILE}" ]; then
    echo "ERROR: State checksum file not found at ${CHECKSUM_FILE}" | tee -a "${LOG_FILE}"
    exit 1
fi

# Calculate original hash
ORIGINAL_HASH=$(sha256sum "${RESULTS_FILE}" | awk '{print $1}')
echo "Original results hash: ${ORIGINAL_HASH}" | tee -a "${LOG_FILE}"

# 2. Set Random Seeds for Reproducibility
# Note: The pipeline uses seed=42 in llm_generator.py and deterministic settings.
# We export these to ensure the environment is consistent.
export PYTHONHASHSEED=42
export SEED=42
export DATA_SEED=42

echo "Set PYTHONHASHSEED=42 for reproducibility" | tee -a "${LOG_FILE}"

# 3. Run the Pipeline
# We run the main entry point. The pipeline respects sample limits defined in config/state
# to ensure we process the same subset.
echo "Running pipeline..." | tee -a "${LOG_FILE}"

cd "${PROJECT_ROOT}"

# Run the main script. 
# We assume the pipeline is idempotent regarding the output file generation 
# if the input data and seed are fixed.
# The script will overwrite analysis_results.json.

python3 code/main.py --mode reproduce --seed 42 2>&1 | tee -a "${LOG_FILE}"

if [ $? -ne 0 ]; then
    echo "ERROR: Pipeline execution failed." | tee -a "${LOG_FILE}"
    exit 1
fi

# 4. Verify Integrity
if [ ! -f "${RESULTS_FILE}" ]; then
    echo "ERROR: Reproduced results file not found after execution." | tee -a "${LOG_FILE}"
    exit 1
fi

NEW_HASH=$(sha256sum "${RESULTS_FILE}" | awk '{print $1}')
echo "Reproduced results hash: ${NEW_HASH}" | tee -a "${LOG_FILE}"

if [ "${ORIGINAL_HASH}" == "${NEW_HASH}" ]; then
    echo "SUCCESS: Hashes match. Results are reproducible." | tee -a "${LOG_FILE}"
    echo "=== Reproducibility Check PASSED ===" | tee -a "${LOG_FILE}"
    exit 0
else
    echo "WARNING: Hashes do not match." | tee -a "${LOG_FILE}"
    echo "Original: ${ORIGINAL_HASH}" | tee -a "${LOG_FILE}"
    echo "New:      ${NEW_HASH}" | tee -a "${LOG_FILE}"
    echo "This may be due to non-deterministic model outputs or data changes." | tee -a "${LOG_FILE}"
    echo "=== Reproducibility Check FAILED (Hash Mismatch) ===" | tee -a "${LOG_FILE}"
    # Exit with 0 for CI non-blocking check as per task description "non-blocking check"
    # But log the failure clearly.
    exit 0 
fi