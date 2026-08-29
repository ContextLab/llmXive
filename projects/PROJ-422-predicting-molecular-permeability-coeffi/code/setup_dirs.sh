#!/bin/bash
#
# setup_dirs.sh
# Creates the project directory structure for PROJ-422-predicting-molecular-permeability-coeffi
#
# Usage: bash setup_dirs.sh
# Verification: bash setup_dirs.sh && ls
#

set -e

# Define the project root relative to the script location or current directory
# The task specifies paths relative to the project root.
# We will create them relative to the current working directory where the script is run.
PROJECT_ROOT="projects/PROJ-422-predicting-molecular-permeability-coeffi"

echo "Creating directory structure for project: $PROJECT_ROOT"

# Define the directories to create
DIRS=(
  "$PROJECT_ROOT/code/data"
  "$PROJECT_ROOT/code/models"
  "$PROJECT_ROOT/code/analysis"
  "$PROJECT_ROOT/data/raw"
  "$PROJECT_ROOT/data/processed"
  "$PROJECT_ROOT/data/interim"
  "$PROJECT_ROOT/results"
  "$PROJECT_ROOT/tests/unit"
  "$PROJECT_ROOT/tests/integration"
)

# Create directories
for dir in "${DIRS[@]}"; do
  if [ ! -d "$dir" ]; then
    mkdir -p "$dir"
    echo "Created: $dir"
  else
    echo "Exists: $dir"
  fi
done

echo ""
echo "Directory creation complete."
echo "Verifying structure..."
echo ""

# Verify structure by listing the root
if [ -d "$PROJECT_ROOT" ]; then
  find "$PROJECT_ROOT" -type d | sort
else
  echo "ERROR: Project root $PROJECT_ROOT was not created."
  exit 1
fi

exit 0