#!/bin/bash
# Script to initialize linting and formatting tools for the project.
# This installs pre-commit and sets up the git hooks.

set -e

echo "Installing development dependencies..."
pip install -r requirements-dev.txt

echo "Initializing pre-commit hooks..."
pre-commit install

echo "Linting and formatting configuration complete."
echo "Run 'pre-commit run --all-files' to check the entire codebase."
echo "Run 'pre-commit run' to check staged files before committing."
