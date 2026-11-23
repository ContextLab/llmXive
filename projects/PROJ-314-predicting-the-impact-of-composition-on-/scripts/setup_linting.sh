#!/bin/bash
# Script to initialize linting and formatting tools for the project

set -e

echo "Installing pre-commit..."
pip install pre-commit

echo "Installing ruff and black..."
pip install ruff black

echo "Initializing pre-commit hooks..."
pre-commit install

echo "Linting and formatting setup complete."
echo "Run 'pre-commit run --all-files' to check all files."
echo "Run 'black .' to format all files."
echo "Run 'ruff check .' to lint all files."
