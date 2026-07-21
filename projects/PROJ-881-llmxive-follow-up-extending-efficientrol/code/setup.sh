#!/bin/bash
# Setup script for llmXive Follow-up: Entropy-Guided Validity Prediction in RL Rollouts
# Creates the required project directory structure

set -e

PROJECT_ROOT="projects/PROJ-881-llmxive-follow-up-extending-efficientrol"
CODE_DIR="$PROJECT_ROOT/code"

# Define all required directories
DIRS=(
    "$CODE_DIR/src"
    "$CODE_DIR/tests"
    "$CODE_DIR/data"
    "$CODE_DIR/docs"
    "$CODE_DIR/scripts"
    "$CODE_DIR/results"
    "$CODE_DIR/specs/001-entropy-validity-prediction/contracts"
    "$PROJECT_ROOT/logs"
    "$PROJECT_ROOT/state"
)

echo "Creating project directory structure..."

# Create all directories
for dir in "${DIRS[@]}"; do
    mkdir -p "$dir"
done

# Verify all directories exist
ALL_EXIST=true
for dir in "${DIRS[@]}"; do
    if [ ! -d "$dir" ]; then
        echo "ERROR: Directory $dir was not created successfully"
        ALL_EXIST=false
    fi
done

if [ "$ALL_EXIST" = false ]; then
    echo "Structure creation failed"
    exit 1
fi

# Generate project_structure.log
LOG_FILE="$CODE_DIR/project_structure.log"
{
    echo "Project Structure Creation Log"
    echo "=============================="
    echo "Timestamp: $(date -Iseconds)"
    echo ""
    echo "Directories created:"
    for dir in "${DIRS[@]}"; do
        echo "  - $dir [EXISTS]"
    done
    echo ""
    echo "Status: SUCCESS"
    echo "Structure created"
} > "$LOG_FILE"

echo "Structure created"
echo "Log file generated: $LOG_FILE"
