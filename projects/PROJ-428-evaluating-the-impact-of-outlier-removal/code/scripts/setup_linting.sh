#!/bin/bash
set -e

echo "Installing development dependencies..."
pip install -r code/requirements-dev.txt

echo "Linting and formatting tools installed."
echo "Run 'bash code/scripts/run_lint.sh' to check code style."
echo "Run 'bash code/scripts/run_format.sh' to format code."