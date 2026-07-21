#!/bin/bash
# Setup script for llmXive Follow-up: Entropy-Guided Validity Prediction in RL Rollouts
# Creates the required directory structure and verifies existence

set -e

PROJECT_ROOT="projects/PROJ-881-llmxive-follow-up-extending-efficientrol"
LOG_FILE="project_structure.log"

# Define all required paths
PATHS=(
    "${PROJECT_ROOT}/code/src"
    "${PROJECT_ROOT}/tests"
    "${PROJECT_ROOT}/data"
    "${PROJECT_ROOT}/docs"
    "${PROJECT_ROOT}/scripts"
    "${PROJECT_ROOT}/results"
    "${PROJECT_ROOT}/specs/001-entropy-validity-prediction/contracts"
)

# Create directories
echo "Creating directory structure..."
for dir in "${PATHS[@]}"; do
    mkdir -p "$dir"
done

# Verify all paths exist
echo "Verifying directory structure..."
ALL_EXIST=true
FAILED_PATHS=()

for dir in "${PATHS[@]}"; do
    if [ ! -d "$dir" ]; then
        ALL_EXIST=false
        FAILED_PATHS+=("$dir")
    fi
done

# Generate log file
{
    echo "Project Structure Creation Log"
    echo "Generated at: $(date)"
    echo "================================"
    echo ""
    if [ "$ALL_EXIST" = true ]; then
        echo "Status: SUCCESS"
        echo "All directories created successfully."
        echo ""
        echo "Directories:"
        for dir in "${PATHS[@]}"; do
            echo "  [OK] $dir"
        done
    else
        echo "Status: FAILED"
        echo "The following directories were not created:"
        for failed in "${FAILED_PATHS[@]}"; do
            echo "  [FAIL] $failed"
        done
    fi
} > "$LOG_FILE"

# Final check
if [ "$ALL_EXIST" = true ]; then
    echo "Structure created"
    exit 0
else
    echo "Structure creation failed"
    exit 1
fi