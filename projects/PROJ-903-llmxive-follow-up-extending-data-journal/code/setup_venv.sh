#!/bin/bash
# Script to create a virtual environment and install dependencies for PROJ-903
# This script assumes requirements.txt is present in the project root.

set -e

echo "=== Setting up Python Virtual Environment for llmXive ==="

# Determine the project root (assuming this script is in code/)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

VENV_DIR="$PROJECT_ROOT/venv"
REQUIREMENTS_FILE="$PROJECT_ROOT/requirements.txt"

if [ ! -f "$REQUIREMENTS_FILE" ]; then
    echo "Error: requirements.txt not found at $REQUIREMENTS_FILE"
    exit 1
fi

echo "Creating virtual environment at $VENV_DIR..."
python3 -m venv "$VENV_DIR"

echo "Activating environment and installing dependencies from requirements.txt..."
source "$VENV_DIR/bin/activate"
python -m pip install --upgrade pip
python -m pip install -r "$REQUIREMENTS_FILE"

echo "=== Setup Complete ==="
echo "To activate the environment manually, run:"
echo "  source $VENV_DIR/bin/activate"
