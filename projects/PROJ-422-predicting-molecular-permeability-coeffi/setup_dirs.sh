#!/bin/bash
# setup_dirs.sh
# Script to programmatically generate the project directory structure
# for PROJ-422-predicting-molecular-permeability-coeffi
#
# Usage: bash setup_dirs.sh && ls
#
# This script creates the following directories relative to the project root:
# - code/data, code/models, code/analysis
# - data/raw, data/processed, data/interim
# - results
# - tests/unit, tests/integration

set -e  # Exit immediately if a command exits with a non-zero status

# Define the project base directory name
PROJECT_DIR="projects/PROJ-422-predicting-molecular-permeability-coeffi"

echo "Creating project directory structure for $PROJECT_DIR..."

# Create the main project directory
mkdir -p "$PROJECT_DIR"

# Create code directories
mkdir -p "$PROJECT_DIR/code/data"
mkdir -p "$PROJECT_DIR/code/models"
mkdir -p "$PROJECT_DIR/code/analysis"

# Create data directories
mkdir -p "$PROJECT_DIR/data/raw"
mkdir -p "$PROJECT_DIR/data/processed"
mkdir -p "$PROJECT_DIR/data/interim"

# Create results directory
mkdir -p "$PROJECT_DIR/results"

# Create tests directories
mkdir -p "$PROJECT_DIR/tests/unit"
mkdir -p "$PROJECT_DIR/tests/integration"

echo "Directory structure created successfully."
echo ""
echo "Verification (listing created structure):"
find "$PROJECT_DIR" -type d | sort

# Optional: Create placeholder .gitkeep files to ensure directories are tracked by git
# Uncomment the following lines if git tracking of empty directories is required:
# touch "$PROJECT_DIR/code/data/.gitkeep"
# touch "$PROJECT_DIR/code/models/.gitkeep"
# touch "$PROJECT_DIR/code/analysis/.gitkeep"
# touch "$PROJECT_DIR/data/raw/.gitkeep"
# touch "$PROJECT_DIR/data/processed/.gitkeep"
# touch "$PROJECT_DIR/data/interim/.gitkeep"
# touch "$PROJECT_DIR/results/.gitkeep"
# touch "$PROJECT_DIR/tests/unit/.gitkeep"
# touch "$PROJECT_DIR/tests/integration/.gitkeep"

exit 0