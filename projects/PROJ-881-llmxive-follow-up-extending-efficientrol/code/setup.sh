#!/bin/bash
# Setup script for llmXive Follow-up project
# Creates required directory structure and verifies existence

set -e

# Project root relative to script execution
PROJECT_ROOT="projects/PROJ-881-llmxive-follow-up-extending-efficientrol"
CODE_DIR="${PROJECT_ROOT}/code"
LOG_FILE="${CODE_DIR}/project_structure.log"

# Define all required directories
DIRS=(
  "${CODE_DIR}"
  "${CODE_DIR}/tests"
  "${CODE_DIR}/data"
  "${CODE_DIR}/docs"
  "${CODE_DIR}/scripts"
  "${CODE_DIR}/results"
  "${PROJECT_ROOT}/specs/001-entropy-validity-prediction/contracts"
  "${CODE_DIR}/src"
  "${CODE_DIR}/data/raw"
  "${CODE_DIR}/data/processed"
  "${CODE_DIR}/artifacts"
  "${CODE_DIR}/state"
)

# Create directories
echo "Creating directory structure..."
for dir in "${DIRS[@]}"; do
  mkdir -p "$dir"
  echo "Created: $dir"
done

# Verify all paths exist and collect absolute paths
echo "Verifying directory structure..."
ABS_PATHS=()
MISSING=0

for dir in "${DIRS[@]}"; do
  if [ ! -d "$dir" ]; then
    echo "ERROR: Missing directory $dir"
    MISSING=1
  else
    # Get absolute path
    ABS_PATH=$(cd "$dir" && pwd)
    ABS_PATHS+=("$ABS_PATH")
  fi
done

# Exit with error if any directories are missing
if [ $MISSING -eq 1 ]; then
  echo "ERROR: Some directories are missing. Exiting with code 1."
  exit 1
fi

# Generate JSON log of absolute paths
echo "Generating project structure log..."
{
  echo "["
  first=true
  for path in "${ABS_PATHS[@]}"; do
    if [ "$first" = true ]; then
      first=false
    else
      echo ","
    fi
    printf '  "%s"' "$path"
  done
  echo ""
  echo "]"
} > "$LOG_FILE"

echo "Setup complete. Log written to: $LOG_FILE"
echo "Total directories created: ${#DIRS[@]}"
