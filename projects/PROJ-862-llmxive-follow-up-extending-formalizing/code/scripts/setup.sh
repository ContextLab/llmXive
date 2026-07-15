#!/bin/bash
# Setup script for llmXive research pipeline
# This script creates a virtual environment and installs dependencies from code/requirements.txt

set -e

# Determine script directory and project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

echo "Project root: $PROJECT_ROOT"
echo "Requirements file: $PROJECT_ROOT/code/requirements.txt"

# Check if requirements.txt exists
if [ ! -f "$PROJECT_ROOT/code/requirements.txt" ]; then
    echo "ERROR: requirements.txt not found at $PROJECT_ROOT/code/requirements.txt"
    exit 1
fi

# Create virtual environment if it doesn't exist
VENV_DIR="$PROJECT_ROOT/venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment at $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
else
    echo "Virtual environment already exists at $VENV_DIR"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies from code/requirements.txt..."
pip install -r "$PROJECT_ROOT/code/requirements.txt"

echo ""
echo "=========================================="
echo "Setup complete!"
echo "=========================================="
echo "To activate the environment, run:"
echo "  source $VENV_DIR/bin/activate"
echo ""
echo "To deactivate, run:"
echo "  deactivate"
echo "=========================================="
