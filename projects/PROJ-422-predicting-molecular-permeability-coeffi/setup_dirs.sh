#!/bin/bash
# Setup script for PROJ-422-predicting-molecular-permeability-coeffi
# Creates the required project directory structure programmatically

set -e  # Exit on any error

PROJECT_ROOT="projects/PROJ-422-predicting-molecular-permeability-coeffi"

echo "Creating project directory structure for $PROJECT_ROOT..."

# Create all required directories
mkdir -p "${PROJECT_ROOT}/code/data"
mkdir -p "${PROJECT_ROOT}/code/models"
mkdir -p "${PROJECT_ROOT}/code/analysis"
mkdir -p "${PROJECT_ROOT}/data/raw"
mkdir -p "${PROJECT_ROOT}/data/processed"
mkdir -p "${PROJECT_ROOT}/data/interim"
mkdir -p "${PROJECT_ROOT}/results"
mkdir -p "${PROJECT_ROOT}/tests/unit"
mkdir -p "${PROJECT_ROOT}/tests/integration"

echo "Directory structure created successfully."
echo "Verifying directories exist..."

# Verification checks as specified in the task
if [ -d "${PROJECT_ROOT}/code/data" ] && \
   [ -d "${PROJECT_ROOT}/code/models" ] && \
   [ -d "${PROJECT_ROOT}/code/analysis" ] && \
   [ -d "${PROJECT_ROOT}/data/raw" ] && \
   [ -d "${PROJECT_ROOT}/data/processed" ] && \
   [ -d "${PROJECT_ROOT}/data/interim" ] && \
   [ -d "${PROJECT_ROOT}/results" ] && \
   [ -d "${PROJECT_ROOT}/tests/unit" ] && \
   [ -d "${PROJECT_ROOT}/tests/integration" ]; then
  echo "All 9 directories exist"
else
  echo "ERROR: One or more directories are missing!"
  exit 1
fi

echo "Setup complete."