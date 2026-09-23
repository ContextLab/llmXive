#!/bin/bash
# Script to install and configure linting and formatting tools
# This script should be run after the virtual environment is activated

set -e

echo "Installing linting and formatting tools..."

# Install ruff, black, and pytest
pip install ruff black pytest pytest-cov mypy

echo "Linting and formatting tools installed successfully."
echo "To run linting: ruff check ."
echo "To run formatting: black ."
echo "To run type checking: mypy src"
echo "To run tests: pytest"
