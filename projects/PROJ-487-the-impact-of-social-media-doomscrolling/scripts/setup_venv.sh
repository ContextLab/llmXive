#!/bin/bash
# Script to initialize Python virtual environment for PROJ-487
# This script creates a venv in the project root and activates it.

set -e

PROJECT_ROOT="projects/PROJ-487-the-impact-of-social-media-doomscrolling"
VENV_DIR="${PROJECT_ROOT}/venv"

echo "Setting up Python virtual environment in ${PROJECT_ROOT}..."

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is not installed or not in PATH."
    exit 1
fi

# Check if venv directory already exists
if [ -d "${VENV_DIR}" ]; then
    echo "Virtual environment already exists at ${VENV_DIR}."
    echo "To recreate, remove the directory first: rm -rf ${VENV_DIR}"
    exit 0
fi

# Create the virtual environment
python3 -m venv "${VENV_DIR}"

echo "Virtual environment created successfully at ${VENV_DIR}."
echo ""
echo "To activate the environment, run:"
echo "  source ${VENV_DIR}/bin/activate"
echo ""
echo "Or on Windows:"
echo "  ${VENV_DIR}\\Scripts\\activate"

# Make the script executable (optional, but good practice)
chmod +x "${VENV_DIR}/bin/activate" 2>/dev/null || true
chmod +x "${VENV_DIR}/Scripts/activate.bat" 2>/dev/null || true

echo "Done."