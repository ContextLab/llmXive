#!/bin/bash
# Setup script for linting (ruff) and formatting (black)
# This script ensures the tools are installed and validates the configuration.

set -e

echo "Installing linting and formatting tools..."
pip install ruff black

echo "Checking configuration validity..."
# Validate ruff config
ruff check --config pyproject.toml --output-format=json . || true

# Validate black config (dry run)
black --config pyproject.toml --check --diff code/ || true

echo "Setup complete. Run 'ruff check code/' and 'black --check code/' to verify."
echo "To format code, run 'black code/' and to lint, run 'ruff check --fix code/'"