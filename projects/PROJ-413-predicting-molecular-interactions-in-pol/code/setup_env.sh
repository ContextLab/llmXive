#!/bin/bash
# Setup script to initialize the virtual environment and install dependencies
# for the llmXive PROJ-413 project.

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${PROJECT_ROOT}/venv"
REQUIREMENTS_FILE="${PROJECT_ROOT}/code/requirements.txt"

echo "=== PROJ-413 Environment Setup ==="
echo "Project Root: ${PROJECT_ROOT}"
echo "Requirements: ${REQUIREMENTS_FILE}"

# Check if requirements file exists
if [ ! -f "${REQUIREMENTS_FILE}" ]; then
    echo "ERROR: requirements.txt not found at ${REQUIREMENTS_FILE}"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "${VENV_DIR}" ]; then
    echo "Creating virtual environment at ${VENV_DIR}..."
    python3 -m venv "${VENV_DIR}"
else
    echo "Virtual environment already exists at ${VENV_DIR}"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source "${VENV_DIR}/bin/activate"

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install dependencies
echo "Installing dependencies from requirements.txt..."
pip install -r "${REQUIREMENTS_FILE}"

echo "=== Setup Complete ==="
echo "Virtual environment is now active. To deactivate, run: deactivate"
echo "To reactivate later, run: source ${VENV_DIR}/bin/activate"
