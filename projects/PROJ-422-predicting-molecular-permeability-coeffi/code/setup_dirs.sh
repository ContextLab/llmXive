#!/bin/bash
# setup_dirs.sh - Create the project directory structure for PROJ-422
#
# This script programmatically generates the required directory tree
# for the molecular permeability prediction project.
#
# Usage: bash setup_dirs.sh
# Verification: bash setup_dirs.sh && ls -R projects/PROJ-422-predicting-molecular-permeability-coeffi

set -e  # Exit immediately if a command exits with a non-zero status

# Define the project root relative to the script's location or current directory
# The task specifies paths relative to the project root.
# We assume the script is run from the project root.
PROJECT_ROOT="projects/PROJ-422-predicting-molecular-permeability-coeffi"

# Define the directory structure to create
DIRECTORIES=(
    "code/data"
    "code/models"
    "code/analysis"
    "data/raw"
    "data/processed"
    "data/interim"
    "results"
    "tests/unit"
    "tests/integration"
)

echo "Creating project directory structure for: $PROJECT_ROOT"

# Create the base project directory if it doesn't exist
mkdir -p "$PROJECT_ROOT"

# Create each subdirectory
for dir in "${DIRECTORIES[@]}"; do
    full_path="${PROJECT_ROOT}/${dir}"
    mkdir -p "$full_path"
    echo "  Created: $full_path"
done

echo ""
echo "Directory structure creation complete."
echo "Verifying structure..."

# List the created structure to verify
# Using 'ls' as requested in the task verification step
ls -R "$PROJECT_ROOT"

echo ""
echo "Setup successful."