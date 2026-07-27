#!/bin/bash
# Setup script for PROJ-881-llmxive-follow-up-extending-efficientrol
# Creates root project directory structure

set -e  # Exit on any error

PROJECT_ROOT="projects/PROJ-881-llmxive-follow-up-extending-efficientrol"

# Create root directories
mkdir -p "${PROJECT_ROOT}/code"
mkdir -p "${PROJECT_ROOT}/tests"
mkdir -p "${PROJECT_ROOT}/data"
mkdir -p "${PROJECT_ROOT}/docs"
mkdir -p "${PROJECT_ROOT}/scripts"
mkdir -p "${PROJECT_ROOT}/results"
mkdir -p "${PROJECT_ROOT}/specs/001-entropy-validity-prediction/contracts"

# Verify all paths exist
REQUIRED_PATHS=(
  "${PROJECT_ROOT}/code"
  "${PROJECT_ROOT}/tests"
  "${PROJECT_ROOT}/data"
  "${PROJECT_ROOT}/docs"
  "${PROJECT_ROOT}/scripts"
  "${PROJECT_ROOT}/results"
  "${PROJECT_ROOT}/specs/001-entropy-validity-prediction/contracts"
)

FAILED=0
for path in "${REQUIRED_PATHS[@]}"; do
  if [ ! -d "$path" ]; then
    echo "Structure creation failed: Missing $path"
    FAILED=1
  fi
done

if [ $FAILED -eq 1 ]; then
  exit 1
fi

echo "Structure created"

# Generate project_structure.log with absolute paths
LOG_FILE="project_structure.log"
echo "[" > "$LOG_FILE"
FIRST=1
for path in "${REQUIRED_PATHS[@]}"; do
  ABS_PATH=$(cd "$path" && pwd)
  if [ $FIRST -eq 1 ]; then
    echo "  \"$ABS_PATH\"" >> "$LOG_FILE"
    FIRST=0
  else
    echo "  ,\"$ABS_PATH\"" >> "$LOG_FILE"
  fi
done
echo "]" >> "$LOG_FILE"