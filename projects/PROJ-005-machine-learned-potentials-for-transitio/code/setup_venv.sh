#!/bin/bash
# Setup Python 3.11 virtual environment and install dependencies for llmXive PROJ-005
# This script assumes Python 3.11 is available in the system PATH.

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${PROJECT_ROOT}/.venv"
REQUIREMENTS_FILE="${PROJECT_ROOT}/requirements.txt"

echo ">>> Project Root: ${PROJECT_ROOT}"
echo ">>> Virtual Environment Path: ${VENV_DIR}"
echo ">>> Requirements File: ${REQUIREMENTS_FILE}"

if [ ! -f "${REQUIREMENTS_FILE}" ]; then
    echo "ERROR: requirements.txt not found at ${REQUIREMENTS_FILE}"
    exit 1
fi

# Check for Python 3.11
if ! python3.11 --version > /dev/null 2>&1; then
    echo "ERROR: Python 3.11 is not installed or not in PATH."
    echo "Please install Python 3.11 and ensure 'python3.11' is accessible."
    exit 1
fi

echo ">>> Creating virtual environment with Python 3.11..."
python3.11 -m venv "${VENV_DIR}"

echo ">>> Activating virtual environment..."
source "${VENV_DIR}/bin/activate"

echo ">>> Upgrading pip, setuptools, and wheel..."
pip install --upgrade pip setuptools wheel

echo ">>> Installing dependencies from requirements.txt..."
pip install -r "${REQUIREMENTS_FILE}"

echo ">>> Verification: Checking installed packages..."
python -c "import torch; import torch_geometric; import sklearn; import shap; import pandas; import numpy; import yaml; import pytest; print('All core dependencies verified successfully.')"

echo ">>> Setup complete. To activate the environment, run:"
echo "    source ${VENV_DIR}/bin/activate"

# Deactivate to ensure script doesn't leak state if sourced incorrectly in some shells,
# though typically users want to stay in the venv. We leave it active for the user.
# deactivate
