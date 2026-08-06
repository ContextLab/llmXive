#!/bin/bash
# Script to create the project directory structure for PROJ-484
# This script implements Task T001: Create project directory structure

set -e

# Define the project root directory
PROJECT_ROOT="projects/PROJ-484-the-impact-of-visual-attention-on-recall"

# Create the project root directory
mkdir -p "$PROJECT_ROOT"

# Change to the project root directory
cd "$PROJECT_ROOT"

# Create the required directory structure
# data/raw: For raw downloaded datasets
# data/processed: For cleaned and analysis-ready data
# artifacts/figures: For generated plots and visualizations
# artifacts/logs: For log files
# code: For Python source code
# tests: For unit and integration tests
mkdir -p data/raw data/processed artifacts/figures artifacts/logs code tests

echo "Directory structure created successfully at $PROJECT_ROOT"
echo "Created directories:"
echo "  - data/raw"
echo "  - data/processed"
echo "  - artifacts/figures"
echo "  - artifacts/logs"
echo "  - code"
echo "  - tests"
