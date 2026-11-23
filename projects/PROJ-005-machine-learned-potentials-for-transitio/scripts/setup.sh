#!/bin/bash
# T005a: Initialize Python environment for llmXive project
# Creates 'code/' directory and sets up a virtualenv there.

set -e  # Exit on any error

# Define paths relative to project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CODE_DIR="${PROJECT_ROOT}/code"
VENV_DIR="${CODE_DIR}/venv"
REQUIREMENTS_FILE="${PROJECT_ROOT}/requirements.txt"

echo "=== llmXive Setup Script ==="
echo "Project Root: ${PROJECT_ROOT}"
echo "Target Directory: ${CODE_DIR}"

# 1. Create the 'code/' directory if it doesn't exist
if [ ! -d "${CODE_DIR}" ]; then
    echo "[1/3] Creating 'code/' directory..."
    mkdir -p "${CODE_DIR}"
else
    echo "[1/3] 'code/' directory already exists."
fi

# 2. Check for requirements.txt
if [ ! -f "${REQUIREMENTS_FILE}" ]; then
    echo "ERROR: requirements.txt not found at ${REQUIREMENTS_FILE}"
    echo "Please ensure T004 (Create requirements.txt) is completed first."
    exit 1
fi

# 3. Set up virtual environment in code/venv
if [ -d "${VENV_DIR}" ]; then
    echo "[2/3] Virtual environment already exists at ${VENV_DIR}. Removing to ensure clean state..."
    rm -rf "${VENV_DIR}"
fi

echo "[2/3] Creating virtual environment at ${VENV_DIR}..."
python3 -m venv "${VENV_DIR}"

# 4. Activate and install dependencies
echo "[3/3] Activating environment and installing dependencies from requirements.txt..."
# Use the activate script directly to avoid shell interaction issues
source "${VENV_DIR}/bin/activate"

# Upgrade pip first
pip install --upgrade pip --quiet

# Install requirements
if [ -f "${REQUIREMENTS_FILE}" ]; then
    pip install -r "${REQUIREMENTS_FILE}" --quiet
    echo "Dependencies installed successfully."
else
    echo "WARNING: requirements.txt not found, skipping dependency installation."
fi

echo "=== Setup Complete ==="
echo "Virtual environment is ready at: ${VENV_DIR}"
echo "To activate manually later, run: source ${VENV_DIR}/bin/activate"