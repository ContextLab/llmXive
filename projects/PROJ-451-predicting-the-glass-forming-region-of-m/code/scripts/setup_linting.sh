#!/bin/bash
# Script to initialize linting and formatting tools for the project
# This script installs ruff and black if not present, and validates configuration

set -e

echo "Setting up linting and formatting tools..."

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is required but not found."
    exit 1
fi

# Install/Upgrade tools
echo "Installing/Upgrading ruff and black..."
pip install --upgrade pip
pip install ruff black

# Verify installation
if ! command -v ruff &> /dev/null; then
    echo "Error: ruff installation failed."
    exit 1
fi

if ! command -v black &> /dev/null; then
    echo "Error: black installation failed."
    exit 1
fi

# Validate configuration files exist
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG_FILE="$PROJECT_ROOT/pyproject.toml"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: Configuration file pyproject.toml not found at $CONFIG_FILE"
    exit 1
fi

echo "Configuration file found: $CONFIG_FILE"

# Run initial check (dry run) to ensure config is valid
echo "Validating configuration..."
ruff check --config "$CONFIG_FILE" --diff . || true
black --check --config "$CONFIG_FILE" --diff . || true

echo "Linting and formatting setup complete."
echo "To format code: black ."
echo "To check linting: ruff check ."
