#!/usr/bin/env bash
set -euo pipefail

# Script to initialize linting and formatting configuration for the project.
# This installs the necessary tools if they are not present and ensures
# configuration files (pyproject.toml) are in place.

echo "Ensuring dev dependencies are installed..."
pip install -e ".[dev]"

echo "Configuration for Ruff and Black is defined in pyproject.toml."
echo "To run linting: ruff check ."
echo "To run formatting: black ."
echo "Setup complete."