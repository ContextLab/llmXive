#!/bin/bash
# Setup script to verify linting and formatting tools are installed and configured

set -e

echo "Checking for required linting and formatting tools..."

# Check for Ruff
if command -v ruff &> /dev/null; then
    echo "✓ Ruff found: $(ruff --version)"
else
    echo "✗ Ruff not found. Installing..."
    pip install ruff
fi

# Check for Black
if command -v black &> /dev/null; then
    echo "✓ Black found: $(black --version)"
else
    echo "✗ Black not found. Installing..."
    pip install black
fi

# Check for isort (optional, used by ruff usually but good to have standalone)
if command -v isort &> /dev/null; then
    echo "✓ isort found: $(isort --version)"
else
    echo "ℹ isort not found. Ruff handles imports, but installing for standalone use..."
    pip install isort
fi

echo ""
echo "Running configuration validation..."

# Validate Ruff config
echo "Validating Ruff configuration..."
ruff check --config pyproject.toml code/src --no-fix || true

# Validate Black config
echo "Validating Black configuration..."
black --check --config pyproject.toml code/src || true

echo ""
echo "Setup complete. Tools are installed and configuration files are present."
echo "To lint: ruff check code/"
echo "To format: black code/"
echo "To auto-fix lint issues: ruff check --fix code/"
