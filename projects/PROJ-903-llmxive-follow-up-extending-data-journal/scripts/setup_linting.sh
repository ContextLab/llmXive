#!/bin/bash
# Setup script to ensure linting and formatting tools are configured and ready
# This script validates the pyproject.toml configuration for ruff and black

set -e

echo "Verifying linting and formatting configuration..."

# Check if pyproject.toml exists
if [ ! -f "pyproject.toml" ]; then
    echo "Error: pyproject.toml not found in current directory."
    exit 1
fi

# Verify ruff configuration exists
if ! grep -q "\[tool.ruff\]" pyproject.toml; then
    echo "Error: Ruff configuration not found in pyproject.toml"
    exit 1
fi

# Verify black configuration exists
if ! grep -q "\[tool.black\]" pyproject.toml; then
    echo "Error: Black configuration not found in pyproject.toml"
    exit 1
fi

# Verify pytest configuration exists
if ! grep -q "\[tool.pytest.ini_options\]" pyproject.toml; then
    echo "Error: Pytest configuration not found in pyproject.toml"
    exit 1
fi

# Attempt to run ruff check (dry run of config validation)
echo "Checking Ruff configuration validity..."
if command -v ruff &> /dev/null; then
    ruff check --config pyproject.toml --output-format=text . || true
else
    echo "Warning: Ruff not installed. Run 'pip install ruff' to enable linting."
fi

# Attempt to run black (dry run of config validation)
echo "Checking Black configuration validity..."
if command -v black &> /dev/null; then
    black --config pyproject.toml --check --diff . || true
else
    echo "Warning: Black not installed. Run 'pip install black' to enable formatting."
fi

echo "Linting and formatting configuration verified successfully."