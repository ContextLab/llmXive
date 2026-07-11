#!/bin/bash
# Setup script to install and configure linting and formatting tools
# for the llmXive automated science pipeline.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "==> Installing linting and formatting tools..."

# Install black, flake8, isort, and mypy
pip install black flake8 isort mypy

echo "==> Verifying configuration files..."

# Check if configuration files exist
if [ ! -f "$PROJECT_ROOT/.flake8" ]; then
    echo "Error: .flake8 configuration file not found in project root."
    exit 1
fi

if [ ! -f "$PROJECT_ROOT/pyproject.toml" ]; then
    echo "Error: pyproject.toml configuration file not found in project root."
    exit 1
fi

echo "==> Configuration verified successfully."
echo ""
echo "To run linters manually:"
echo "  flake8 code/"
echo ""
echo "To run formatters manually:"
echo "  black code/"
echo "  isort code/"
echo ""
echo "To run type checker:"
echo "  mypy code/"
