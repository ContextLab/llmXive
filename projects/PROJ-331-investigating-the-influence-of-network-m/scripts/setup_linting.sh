#!/bin/bash
# Script to initialize linting and formatting tools for the project
# This installs pre-commit hooks and verifies configuration

set -e

echo "Installing development dependencies..."
pip install -r requirements-dev.txt

echo "Initializing pre-commit hooks..."
pre-commit install

echo "Running a quick lint check on existing files..."
# Run flake8 on code directory if files exist
if [ -d "code" ]; then
    echo "Checking code/ with flake8..."
    flake8 code/ --config=.flake8 || echo "Lint warnings found (non-fatal in setup)"
fi

echo "Linting and formatting configuration complete."
echo "To run manually: pre-commit run --all-files"