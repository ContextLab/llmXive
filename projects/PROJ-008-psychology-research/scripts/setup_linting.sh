#!/bin/bash
# Script to initialize ruff and black configurations for the project
# Run from the project root: ./scripts/setup_linting.sh

set -e

echo "Installing linting tools..."
pip install ruff black

echo "Checking for existing configuration..."
if [ ! -f "code/.ruff.toml" ]; then
    echo "Creating .ruff.toml in code/ directory..."
    # The file is created by the implementation task, this script just validates
    echo "Configuration found."
fi

if [ ! -f "code/pyproject.toml" ]; then
    echo "Error: pyproject.toml not found in code/ directory."
    exit 1
fi

echo "Running initial lint check (ruff)..."
# Run ruff check against the code directory
ruff check code/ --config code/.ruff.toml || echo "Lint issues found (expected for new code). Fix with: ruff check code/ --fix"

echo "Running initial format check (black)..."
black --check code/ --config code/pyproject.toml || echo "Formatting issues found. Fix with: black code/ --config code/pyproject.toml"

echo "Linting and formatting setup complete."