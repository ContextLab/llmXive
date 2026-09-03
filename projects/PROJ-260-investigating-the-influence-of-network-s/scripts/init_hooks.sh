#!/bin/bash
# Initialize pre-commit hooks for ruff and black
# This script should be run after installing the dev dependencies

set -e

echo "Installing pre-commit hooks..."
pre-commit install
echo "Pre-commit hooks installed successfully."
echo "Run 'pre-commit run --all-files' to check the entire codebase."
