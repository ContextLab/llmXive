#!/bin/bash
# setup.sh - Initialize project structure for PROJ-451
# This script creates the necessary directory hierarchy and placeholder files
# for the Glass Forming Region prediction project.

set -e  # Exit immediately if a command exits with a non-zero status

# Define the project root directory
PROJECT_ROOT="projects/PROJ-451-predicting-the-glass-forming-region-of-m"

echo "Initializing project structure for $PROJECT_ROOT..."

# Create the main project directory and subdirectories
# Using -p ensures no error if directories already exist
mkdir -p "${PROJECT_ROOT}/code"
mkdir -p "${PROJECT_ROOT}/data/raw"
mkdir -p "${PROJECT_ROOT}/data/processed"
mkdir -p "${PROJECT_ROOT}/tests"
mkdir -p "${PROJECT_ROOT}/docs"
mkdir -p "${PROJECT_ROOT}/notebooks"

# Create placeholder .gitkeep files to ensure directories are tracked by git
# even if they are empty
touch "${PROJECT_ROOT}/data/raw/.gitkeep"
touch "${PROJECT_ROOT}/data/processed/.gitkeep"

# Verify the structure was created
if [ -d "${PROJECT_ROOT}" ]; then
    echo "Project root created: ${PROJECT_ROOT}"
else
    echo "ERROR: Failed to create project root."
    exit 1
fi

if [ -d "${PROJECT_ROOT}/code" ] && \
   [ -d "${PROJECT_ROOT}/data" ] && \
   [ -d "${PROJECT_ROOT}/tests" ] && \
   [ -d "${PROJECT_ROOT}/docs" ] && \
   [ -d "${PROJECT_ROOT}/notebooks" ]; then
    echo "All required subdirectories created successfully."
else
    echo "ERROR: Missing required subdirectories."
    exit 1
fi

if [ -f "${PROJECT_ROOT}/data/raw/.gitkeep" ] && \
   [ -f "${PROJECT_ROOT}/data/processed/.gitkeep" ]; then
    echo "Placeholder .gitkeep files created successfully."
else
    echo "ERROR: Failed to create .gitkeep files."
    exit 1
fi

echo "Project setup complete."