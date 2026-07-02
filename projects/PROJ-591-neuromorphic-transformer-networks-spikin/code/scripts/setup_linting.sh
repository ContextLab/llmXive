#!/bin/bash
set -e

echo "Installing pre-commit hooks for linting and formatting..."

# Install pre-commit if not present
pip install pre-commit --quiet

# Install the hooks
pre-commit install

echo "Linting setup complete. Run 'pre-commit run --all-files' to check all files."