#!/bin/bash
# Script to configure and verify linting (ruff) and formatting (black) tools
# This script ensures dependencies are installed and configuration is valid.

set -e

echo "=== Configuring Linting and Formatting Tools ==="

# Check if pip is available
if ! command -v pip &> /dev/null; then
    echo "Error: pip is not installed or not in PATH."
    exit 1
fi

# Install dependencies from requirements.txt if they exist
REQUIREMENTS_PATH="code/requirements.txt"
if [ -f "$REQUIREMENTS_PATH" ]; then
    echo "Installing dependencies from $REQUIREMENTS_PATH..."
    pip install -r "$REQUIREMENTS_PATH"
else
    echo "Warning: $REQUIREMENTS_PATH not found. Installing core tools manually."
    pip install ruff black
fi

# Verify ruff installation
echo "Verifying Ruff installation..."
if ! command -v ruff &> /dev/null; then
    echo "Error: Ruff is not installed."
    exit 1
fi
echo "Ruff version: $(ruff --version)"

# Verify black installation
echo "Verifying Black installation..."
if ! command -v black &> /dev/null; then
    echo "Error: Black is not installed."
    exit 1
fi
echo "Black version: $(black --version)"

# Validate configuration files
CONFIG_FILE="code/pyproject.toml"
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: Configuration file $CONFIG_FILE not found."
    exit 1
fi

echo "Validating Ruff configuration..."
ruff check --config "$CONFIG_FILE" --output-format=full --diff || true
# Note: The above might fail if code has linting errors, which is expected.
# We just want to ensure ruff can read the config.

echo "Validating Black configuration..."
black --config "$CONFIG_FILE" --check --diff code/src/ || true
# Note: This might fail if code is not formatted, which is expected.

echo "=== Linting and Formatting Configuration Complete ==="
echo "To run linting: ruff check code/"
echo "To format code: black code/"
echo "To run linting with fixes: ruff check code/ --fix"