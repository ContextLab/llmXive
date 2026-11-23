#!/bin/bash
# Script to install and verify linting tools
set -e

echo "Installing linting tools (ruff, black)..."
pip install ruff black pytest

echo "Verifying installation..."
ruff --version
black --version
pytest --version

echo "Running initial format check (dry run)..."
black --check code/ tests/ || true
ruff check code/ tests/ || true

echo "Linting setup complete. Run 'make format' to auto-fix issues."