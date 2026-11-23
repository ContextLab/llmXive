#!/bin/bash
# T001: Initialize project directory structure for gene essentiality analysis
# Creates standard directories for code, data (raw/processed/phylogeny), results, and tests.

set -e  # Exit immediately if a command exits with a non-zero status

# Define project root (assumes script is run from project root)
PROJECT_ROOT="."

echo "Initializing project structure for PROJ-452..."

# Create directories
mkdir -p "${PROJECT_ROOT}/code"
mkdir -p "${PROJECT_ROOT}/data/raw"
mkdir -p "${PROJECT_ROOT}/data/processed"
mkdir -p "${PROJECT_ROOT}/data/phylogeny"
mkdir -p "${PROJECT_ROOT}/results"
mkdir -p "${PROJECT_ROOT}/tests"
mkdir -p "${PROJECT_ROOT}/scripts"
mkdir -p "${PROJECT_ROOT}/state"
mkdir -p "${PROJECT_ROOT}/contracts"
mkdir -p "${PROJECT_ROOT}/results/null_distribution"

# Create placeholder READMEs to ensure directories are tracked by git
echo "# Code Directory" > "${PROJECT_ROOT}/code/README.md"
echo "# Raw Data" > "${PROJECT_ROOT}/data/raw/README.md"
echo "# Processed Data" > "${PROJECT_ROOT}/data/processed/README.md"
echo "# Phylogeny Data" > "${PROJECT_ROOT}/data/phylogeny/README.md"
echo "# Analysis Results" > "${PROJECT_ROOT}/results/README.md"
echo "# Test Suite" > "${PROJECT_ROOT}/tests/README.md"
echo "# State Management" > "${PROJECT_ROOT}/state/README.md"
echo "# Contracts & Schemas" > "${PROJECT_ROOT}/contracts/README.md"
echo "# Null Model Results" > "${PROJECT_ROOT}/results/null_distribution/README.md"

echo "Directory structure created successfully:"
ls -la "${PROJECT_ROOT}"
echo "Subdirectories:"
ls -d "${PROJECT_ROOT}"/code "${PROJECT_ROOT}"/data "${PROJECT_ROOT}"/results "${PROJECT_ROOT}"/tests 2>/dev/null || true
echo "Done."