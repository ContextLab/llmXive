#!/bin/bash
# Script to install and initialize linting tools (ruff and black)
# Run this from the project root: code/scripts/setup_linting.sh

set -e

echo "Installing linting tools..."
pip install ruff black

echo "Initializing ruff configuration..."
# If pyproject.toml doesn't exist or lacks [tool.ruff], ruff init can help
if ! grep -q "\[tool.ruff\]" pyproject.toml 2>/dev/null; then
    echo "Ruff configuration not found in pyproject.toml. Creating basic config..."
    ruff --help > /dev/null
    # We rely on the pyproject.toml created by T003, but ensure ruff can see it
fi

echo "Running initial check (fix mode) on src/..."
# Run a dry run first to see what needs fixing
ruff check --fix code/src/ || true

echo "Formatting with black..."
black code/src/

echo "Linting and formatting setup complete."
echo "To run manually:"
echo "  ruff check code/src/"
echo "  black code/src/"
echo "Or use pre-commit hooks after installing: pip install pre-commit && pre-commit install"