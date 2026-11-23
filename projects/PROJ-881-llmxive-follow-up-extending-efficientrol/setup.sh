#!/bin/bash
# setup.sh - Create root project directory structure for llmXive Follow-up
# Project: PROJ-881-llmxive-follow-up-extending-efficientrol

set -e

PROJECT_ROOT="projects/PROJ-881-llmxive-follow-up-extending-efficientrol"
LOG_FILE="project_structure.log"

echo "Creating directory structure for $PROJECT_ROOT..."

# Core directories
mkdir -p "${PROJECT_ROOT}/code"
mkdir -p "${PROJECT_ROOT}/tests"
mkdir -p "${PROJECT_ROOT}/data"
mkdir -p "${PROJECT_ROOT}/docs"
mkdir -p "${PROJECT_ROOT}/scripts"
mkdir -p "${PROJECT_ROOT}/results"
mkdir -p "${PROJECT_ROOT}/specs/001-entropy-validity-prediction/contracts"

# Subdirectories under code/
mkdir -p "${PROJECT_ROOT}/code/src"
mkdir -p "${PROJECT_ROOT}/code/data/raw"
mkdir -p "${PROJECT_ROOT}/code/data/processed"
mkdir -p "${PROJECT_ROOT}/code/artifacts"
mkdir -p "${PROJECT_ROOT}/code/state"
mkdir -p "${PROJECT_ROOT}/code/logs"
mkdir -p "${PROJECT_ROOT}/code/src/utils"
mkdir -p "${PROJECT_ROOT}/code/src/data"
mkdir -p "${PROJECT_ROOT}/code/src/generation"
mkdir -p "${PROJECT_ROOT}/code/src/analysis"
mkdir -p "${PROJECT_ROOT}/code/tests/unit"
mkdir -p "${PROJECT_ROOT}/code/tests/integration"
mkdir -p "${PROJECT_ROOT}/code/tests/contract"

echo "Directory creation complete."
echo "Running verification..."

# Run verification script
python "${PROJECT_ROOT}/scripts/verify_structure.py" "${PROJECT_ROOT}"

exit_code=$?
if [ $exit_code -eq 0 ]; then
    echo "Verification successful. Structure is valid."
    echo "$(date -Iseconds) - Setup completed successfully" >> "${LOG_FILE}"
else
    echo "Verification failed. Check ${LOG_FILE} for details."
    echo "$(date -Iseconds) - Setup FAILED" >> "${LOG_FILE}"
    exit 1
fi
