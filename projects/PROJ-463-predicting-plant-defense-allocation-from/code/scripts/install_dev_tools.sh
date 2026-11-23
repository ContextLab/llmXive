#!/bin/bash
# Script to install and verify linting and formatting tools
# This script ensures ruff and black are available in the environment

set -e

echo "Installing development tools..."

# Install ruff and black using pip
python -m pip install --upgrade pip
python -m pip install ruff black pytest pytest-cov

echo "Verifying installations..."

# Verify black
if python -m black --version; then
    echo "✓ Black installed successfully"
else
    echo "✗ Black installation failed"
    exit 1
fi

# Verify ruff
if python -m ruff --version; then
    echo "✓ Ruff installed successfully"
else
    echo "✗ Ruff installation failed"
    exit 1
fi

echo "All development tools installed and verified."
echo ""
echo "To format code:    python -m black code/"
echo "To lint code:      python -m ruff check code/"
echo "To run tests:      python -m pytest tests/"
