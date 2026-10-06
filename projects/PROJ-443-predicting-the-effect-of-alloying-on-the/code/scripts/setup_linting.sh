#!/bin/bash
# Setup linting and formatting tools for the project

set -e

echo "Installing development dependencies..."
pip install -r code/requirements-dev.txt

echo "Installing pre-commit hooks..."
cd code && pre-commit install

echo "Linting configuration complete."
echo "Run 'pre-commit run --all-files' to check all files."
echo "Run 'black code/' to format code."
echo "Run 'flake8 code/' to check linting rules."