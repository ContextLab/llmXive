#!/bin/bash
# Script to create the required project directory structure for PROJ-476
# This script corresponds to task T001

set -e

# Create code directories
mkdir -p code/data
mkdir -p code/analysis
mkdir -p code/viz
mkdir -p code/tests

# Create artifacts directories
mkdir -p artifacts/figures
mkdir -p artifacts/reports

# Create state directory
mkdir -p state

echo "Project structure created successfully."
echo "Directories:"
ls -R code artifacts state
