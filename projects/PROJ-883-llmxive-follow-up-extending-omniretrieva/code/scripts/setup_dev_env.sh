#!/bin/bash
set -e

echo "Setting up development environment for llmXive research..."

# Check for Python 3.11
if ! command -v python3.11 &> /dev/null; then
    echo "Error: Python 3.11 is required but not found."
    echo "Please install Python 3.11 or set your default python to 3.11."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3.11 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing project dependencies..."
pip install -r requirements.txt

# Install dev dependencies
echo "Installing development tools (ruff, black)..."
pip install -e ".[dev]"

echo "Setup complete!"
echo "To activate the environment, run: source venv/bin/activate"
echo "To format code, run: make format"
echo "To run linters, run: make lint"
echo "To run tests, run: make test"
