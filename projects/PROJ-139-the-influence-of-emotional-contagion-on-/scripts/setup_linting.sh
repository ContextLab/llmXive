#!/bin/bash
# Setup script for linting and formatting tools
# This script installs pre-commit hooks and validates the environment

set -e

echo "Installing pre-commit hooks..."
python -m pip install --upgrade pip
python -m pip install pre-commit black ruff

echo "Installing pre-commit hooks to .git/hooks..."
pre-commit install

echo "Running a quick format check on the codebase..."
black --check --diff code/ || true
ruff check code/ || true

echo "Setup complete. Run 'pre-commit run --all-files' to check all files."
echo "Run 'black code/' and 'ruff --fix code/' to auto-fix issues."
