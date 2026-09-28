#!/bin/bash
# setup_python_env.sh
# Initializes the Python 3.11 environment and installs dependencies.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
REQUIREMENTS_FILE="$SCRIPT_DIR/requirements.txt"

echo "=== Setting up Python Environment for PROJ-677 ==="

# Check for Python 3.11
if ! command -v python3.11 &> /dev/null; then
    echo "WARNING: Python 3.11 not found. Attempting to use system python3."
    PYTHON_CMD="python3"
else
    PYTHON_CMD="python3.11"
fi

if ! $PYTHON_CMD --version &> /dev/null; then
    echo "ERROR: No suitable Python 3.x interpreter found."
    exit 1
fi

echo "Using Python: $($PYTHON_CMD --version)"

# Create virtual environment if it doesn't exist
VENV_DIR="$PROJECT_ROOT/venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment at $VENV_DIR..."
    $PYTHON_CMD -m venv "$VENV_DIR"
else
    echo "Virtual environment already exists at $VENV_DIR."
fi

# Activate and install
source "$VENV_DIR/bin/activate"

echo "Installing dependencies from requirements.txt..."
if [ -f "$REQUIREMENTS_FILE" ]; then
    pip install --upgrade pip
    pip install -r "$REQUIREMENTS_FILE"
    echo "Dependencies installed successfully."
else
    echo "WARNING: requirements.txt not found at $REQUIREMENTS_FILE. Skipping pip install."
fi

echo "=== Environment Setup Complete ==="
echo "To activate the environment manually, run: source $VENV_DIR/bin/activate"