#!/bin/bash
# Script to create the project directory structure for llmXive project PROJ-476
# This script implements Task T001 by creating all required directories.

set -e

# Create code subdirectories
mkdir -p code/data
mkdir -p code/analysis
mkdir -p code/viz
mkdir -p code/tests

# Create artifacts subdirectories
mkdir -p artifacts/figures
mkdir -p artifacts/reports

# Create state directory
mkdir -p state

echo "Project structure created successfully."
echo "Directories created:"
echo "  - code/data"
echo "  - code/analysis"
echo "  - code/viz"
echo "  - code/tests"
echo "  - artifacts/figures"
echo "  - artifacts/reports"
echo "  - state"
