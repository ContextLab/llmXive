#!/bin/bash
# Script to initialize a Python 3.11 virtual environment for the project.
# This script ensures Python 3.11 is available and creates the .venv directory.

set -e

PROJECT_ROOT="projects/PROJ-227-assessing-the-trade-offs-between-static-"
VENV_DIR="${PROJECT_ROOT}/.venv"

echo "Checking for Python 3.11..."
# Try to find python3.11, then fallback to checking version of generic python3
if command -v python3.11 &> /dev/null; then
    PYTHON_CMD="python3.11"
elif python3 --version 2>&1 | grep -q "Python 3.11"; then
    PYTHON_CMD="python3"
else
    echo "ERROR: Python 3.11 is not installed or not found in PATH."
    echo "Please install Python 3.11 and ensure it is accessible as 'python3.11' or 'python3'."
    exit 1
fi

echo "Using Python: $(which $PYTHON_CMD) ($($PYTHON_CMD --version))"

echo "Creating virtual environment at ${VENV_DIR}..."
$PYTHON_CMD -m venv "${VENV_DIR}"

echo "Virtual environment created successfully."
echo "To activate, run: source ${VENV_DIR}/bin/activate"
echo "To verify version after activation, run: source ${VENV_DIR}/bin/activate && python --version"

# Verify the version immediately in the script (optional but helpful)
# We use the venv's python directly to check without activating in the current shell
VENV_PYTHON="${VENV_DIR}/bin/python"
if [ -f "$VENV_PYTHON" ]; then
    ACTUAL_VERSION=$($VENV_PYTHON --version)
    echo "Verification: The virtual environment python reports: $ACTUAL_VERSION"
else
    echo "WARNING: Could not verify venv python executable immediately."
fi