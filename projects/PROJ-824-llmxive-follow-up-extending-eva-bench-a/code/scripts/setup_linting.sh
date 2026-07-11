#!/bin/bash
# Setup script to install and configure linting (ruff) and formatting (black) tools.
# This script should be run after `pip install -r requirements.txt` or as part of the 
# initial project setup.

set -e

echo "Installing linting and formatting tools..."

# Install ruff and black via pip (assuming requirements.txt was updated in T002)
# If requirements.txt was not updated yet, install directly:
pip install ruff black

echo "Linting and formatting tools installed successfully."
echo ""
echo "Usage:"
echo "  Format code:   black code/"
echo "  Check format:  black --check code/"
echo "  Lint code:     ruff check code/"
echo "  Fix lint:      ruff check --fix code/"
echo ""
echo "To run all checks before committing, consider adding a pre-commit hook."
