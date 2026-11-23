#!/bin/bash
# Setup linting and formatting tools for llmXive project
# This script installs pre-commit hooks and verifies tool availability.

set -e

echo "Installing development dependencies..."
pip install -q pre-commit ruff black

echo "Initializing pre-commit hooks..."
pre-commit install

echo "Verifying tools..."
ruff --version
black --version

echo "Linting setup complete. Run 'pre-commit run --all-files' to check."
