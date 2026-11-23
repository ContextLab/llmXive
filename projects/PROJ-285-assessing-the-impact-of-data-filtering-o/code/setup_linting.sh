#!/bin/bash
# Setup script to install linting and formatting tools and verify configuration

set -e

echo "Installing development dependencies..."
pip install -r requirements-dev.txt

echo "Verifying flake8 configuration..."
if [ -f ".flake8" ]; then
    echo "✓ .flake8 found"
else
    echo "✗ .flake8 not found"
    exit 1
fi

echo "Verifying pyproject.toml configuration..."
if [ -f "pyproject.toml" ]; then
    echo "✓ pyproject.toml found"
else
    echo "✗ pyproject.toml not found"
    exit 1
fi

echo "Running a quick syntax check on src files..."
python -m flake8 src/ --count --select=E9,F63,F7,F82 --show-source --statistics || true

echo "Linting and formatting setup complete!"