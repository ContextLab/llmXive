#!/bin/bash
# Setup script to install and configure linting tools
# This script ensures flake8, black, and pre-commit are installed
# and initializes the pre-commit hooks in the local repository.

set -e

echo "Installing linting tools (flake8, black, pre-commit)..."
pip install -q black flake8 pre-commit

echo "Initializing pre-commit hooks..."
pre-commit install

echo "Linting setup complete. Run 'pre-commit run --all-files' to check code."
