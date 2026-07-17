#!/bin/bash
# Validate Quickstart Script for PROJ-596 Memory Palaces
# This script runs a minimal end-to-end pipeline and verifies artifact generation.

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CODE_DIR="${PROJECT_ROOT}/code"
ARTIFACTS_DIR="${PROJECT_ROOT}/artifacts/results"
OUTPUT_FILE="${ARTIFACTS_DIR}/run_summary.json"
TIME_LIMIT=18000  # 5 hours in seconds (matching T017c constraint)

echo "=== PROJ-596 Quickstart Validation ==="
echo "Project Root: ${PROJECT_ROOT}"
echo "Output Target: ${OUTPUT_FILE}"
echo "Time Limit: ${TIME_LIMIT} seconds"
echo ""

# Ensure artifacts directory exists
mkdir -p "${ARTIFACTS_DIR}"

# Clean previous run summary if it exists
if [ -f "${OUTPUT_FILE}" ]; then
    echo "Removing existing run summary..."
    rm -f "${OUTPUT_FILE}"
fi

# Change to code directory to ensure imports work
cd "${CODE_DIR}"

echo "Starting pipeline execution..."
START_TIME=$(date +%s)

# Execute the main pipeline
# We run with a timeout to prevent hanging indefinitely
if timeout ${TIME_LIMIT} python main.py; then
    END_TIME=$(date +%s)
    ELAPSED=$((END_TIME - START_TIME))
    echo ""
    echo "Pipeline completed successfully in ${ELAPSED} seconds."

    # Verify output file exists
    if [ -f "${OUTPUT_FILE}" ]; then
        echo "SUCCESS: ${OUTPUT_FILE} generated."
        
        # Basic validation of JSON structure
        if python -c "import json; data = json.load(open('${OUTPUT_FILE}')); assert 'seeds' in data and 'accuracies' in data and 'runtime_seconds' in data"; then
            echo "SUCCESS: Output JSON contains required fields (seeds, accuracies, runtime_seconds)."
            echo ""
            echo "=== Validation Passed ==="
            exit 0
        else
            echo "FAILURE: Output JSON missing required fields."
            exit 1
        fi
    else
        echo "FAILURE: ${OUTPUT_FILE} was not generated."
        exit 1
    fi
else
    EXIT_CODE=$?
    END_TIME=$(date +%s)
    ELAPSED=$((END_TIME - START_TIME))
    
    if [ $EXIT_CODE -eq 124 ]; then
        echo "FAILURE: Pipeline exceeded time limit of ${TIME_LIMIT} seconds (ran for ${ELAPSED}s)."
    else
        echo "FAILURE: Pipeline failed with exit code ${EXIT_CODE}."
    fi
    exit 1
fi
