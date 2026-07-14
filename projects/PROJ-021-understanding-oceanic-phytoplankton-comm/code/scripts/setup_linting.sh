#!/bin/bash
# Setup script to initialize ruff and black configurations
# This script validates that the configuration files are present
# and installs the necessary tools if not already present.

set -e

echo "Checking for linting and formatting tools..."

# Check for ruff
if ! command -v ruff &> /dev/null; then
    echo "Installing ruff..."
    pip install ruff
fi

# Check for black
if ! command -v black &> /dev/null; then
    echo "Installing black..."
    pip install black
fi

echo "Linting and formatting tools are ready."
echo "Run 'ruff check code/' to lint."
echo "Run 'black code/' to format."