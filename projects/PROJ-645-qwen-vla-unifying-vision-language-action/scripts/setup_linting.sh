#!/bin/bash
# Script to install and configure linting and formatting tools
# Prerequisites: Python >= 3.9, pip

set -e

echo "Installing development dependencies..."
pip install -e ".[dev]"

echo "Verifying installation..."
ruff --version
black --version
pytest --version

echo "Linting and formatting tools installed successfully."
echo "To format code: black src/ tests/"
echo "To lint code: ruff check src/ tests/"