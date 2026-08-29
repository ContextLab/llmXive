#!/bin/bash
# T001: Create project directory structure for PROJ-422
# This script programmatically generates the required directory tree.
# Verification: bash setup_dirs.sh && ls -R projects/PROJ-422-predicting-molecular-permeability-coeffi

set -e

PROJECT_ROOT="projects/PROJ-422-predicting-molecular-permeability-coeffi"

echo "Creating directory structure for ${PROJECT_ROOT}..."

# Define the required directories
DIRS=(
  "${PROJECT_ROOT}/code/data"
  "${PROJECT_ROOT}/code/models"
  "${PROJECT_ROOT}/code/analysis"
  "${PROJECT_ROOT}/data/raw"
  "${PROJECT_ROOT}/data/processed"
  "${PROJECT_ROOT}/data/interim"
  "${PROJECT_ROOT}/results"
  "${PROJECT_ROOT}/tests/unit"
  "${PROJECT_ROOT}/tests/integration"
)

# Create directories
for dir in "${DIRS[@]}"; do
  mkdir -p "$dir"
  echo "Created: $dir"
done

# Verify creation by listing the tree
echo ""
echo "Verifying structure..."
if [ -d "${PROJECT_ROOT}" ]; then
  echo "SUCCESS: Project root exists."
  echo "Directory listing:"
  find "${PROJECT_ROOT}" -type d | sort
else
  echo "ERROR: Project root was not created."
  exit 1
fi

echo ""
echo "T001 Setup Complete."
