#!/bin/bash
# Setup script to install and configure linting and formatting tools
# for the llmXive project.

set -e

echo "Installing linting and formatting tools..."

# Install ruff and black via pip
pip install ruff black

# Verify installation
echo "Verifying installations..."
ruff --version
black --version

echo "Linting and formatting tools configured successfully."
echo "To format code: black ."
echo "To lint code: ruff check ."
