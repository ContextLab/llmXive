#!/bin/bash
# T001: Project Structure Initialization Script
# Creates the required directory hierarchy for PROJ-044 and generates a tree visualization.
# References T000 (Spec Alignment) and plan.md Gap Analysis for project scope.

set -e

# Define the project root relative to where this script is executed.
# The task requires the structure to be under projects/PROJ-044-evaluating-the-effectiveness-of-differen/
# We assume the script is run from the repository root or the script directory.
# We will target the specific project folder path.
PROJECT_ROOT="projects/PROJ-044-evaluating-the-effectiveness-of-differen"

echo "Initializing project structure for PROJ-044..."
echo "Target directory: ${PROJECT_ROOT}"

# Create the directory structure
mkdir -p "${PROJECT_ROOT}/code/data"
mkdir -p "${PROJECT_ROOT}/code/training"
mkdir -p "${PROJECT_ROOT}/code/analysis"
mkdir -p "${PROJECT_ROOT}/code/models"
mkdir -p "${PROJECT_ROOT}/tests/unit"
mkdir -p "${PROJECT_ROOT}/tests/integration"
mkdir -p "${PROJECT_ROOT}/data/raw"
mkdir -p "${PROJECT_ROOT}/data/partitions"
mkdir -p "${PROJECT_ROOT}/results"
mkdir -p "${PROJECT_ROOT}/artifacts"

# Verify creation
if [ ! -d "${PROJECT_ROOT}" ]; then
    echo "ERROR: Failed to create project root directory."
    exit 1
fi

echo "Directories created successfully."

# Generate tree output
# Check if 'tree' command is available, if not, use 'find' as a fallback for listing
TREE_OUTPUT_FILE="${PROJECT_ROOT}/tree_output.txt"

if command -v tree &> /dev/null; then
    echo "Generating tree visualization using 'tree' command..."
    cd "${PROJECT_ROOT}"
    tree . > "${TREE_OUTPUT_FILE}" 2>&1 || {
        # Fallback if tree fails (e.g., permission issues or empty dirs not shown)
        find . -type d | sort > "${TREE_OUTPUT_FILE}"
        echo "Warning: 'tree' command had issues, using 'find' fallback."
    }
    cd - > /dev/null
else
    echo "'tree' command not found. Using 'find' to generate directory listing..."
    cd "${PROJECT_ROOT}"
    find . -type d | sort > "${TREE_OUTPUT_FILE}"
    cd - > /dev/null
fi

if [ ! -f "${TREE_OUTPUT_FILE}" ]; then
    echo "ERROR: Failed to generate ${TREE_OUTPUT_FILE}."
    exit 1
fi

echo "Project structure initialization complete."
echo "Directory tree saved to: ${TREE_OUTPUT_FILE}"
echo "Contents of ${TREE_OUTPUT_FILE}:"
cat "${TREE_OUTPUT_FILE}"
