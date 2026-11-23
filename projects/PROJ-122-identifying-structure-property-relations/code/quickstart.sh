#!/bin/bash
# Quickstart script to initialize the project structure and verify environment

set -e

echo "=== LLMXive Project Initialization ==="

# Check Python version
python_version=$(python --version 2>&1 | cut -d' ' -f2)
echo "Python version: $python_version"
if [[ ! "$python_version" =~ ^3\.1[1-9] ]]; then
    echo "Error: Python 3.11 or higher is required."
    exit 1
fi

# Create directory structure
echo "Creating directory structure..."
python code/setup_directories.py

# Create state structure
echo "Creating state structure..."
python code/setup_state.py

# Install dependencies (if not already done)
if [ ! -d "code/venv" ] && [ ! -d ".venv" ]; then
    echo "Installing dependencies..."
    if [ -f "code/requirements.txt" ]; then
        pip install -r code/requirements.txt
    else
        echo "Warning: requirements.txt not found. Please install dependencies manually."
    fi
fi

# Run basic tests
echo "Running basic tests..."
python -m pytest code/tests/ -v

echo "=== Initialization Complete ==="
echo "Project structure is ready. You can now proceed with task implementation."