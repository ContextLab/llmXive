#!/bin/bash
# Setup script for PROJ-503-predicting-plant-defense-compound-produc
# Creates the exact directory structure required by the project specification.

set -e

# Define the project root relative to script location or current working directory
# The task requires paths relative to the project root.
# We assume this script is run from the project root or we derive it.
# To be safe and compliant with "Stay inside the project tree", we use relative paths
# assuming the script is executed from the repo root.

PROJECT_ROOT="projects/PROJ-503-predicting-plant-defense-compound-produc"

# Create the required directories using mkdir -p
# This ensures parent directories are created if they don't exist
# and no error is thrown if they already exist.

mkdir -p "${PROJECT_ROOT}/code/"
mkdir -p "${PROJECT_ROOT}/data/raw/"
mkdir -p "${PROJECT_ROOT}/data/processed/"
mkdir -p "${PROJECT_ROOT}/logs/"
mkdir -p "${PROJECT_ROOT}/outputs/models/"
mkdir -p "${PROJECT_ROOT}/docs/"
mkdir -p "${PROJECT_ROOT}/tests/contract/"
mkdir -p "${PROJECT_ROOT}/tests/integration/"
mkdir -p "${PROJECT_ROOT}/tests/unit/"
mkdir -p "${PROJECT_ROOT}/scripts/"

# Verify creation (optional but good practice for a setup script)
# We echo the created structure to stdout as evidence of execution
echo "Project directory structure created successfully:"
find "${PROJECT_ROOT}" -type d | sort
