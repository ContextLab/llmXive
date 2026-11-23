#!/bin/bash
set -e

echo "Running Black formatter..."
black code/ src/ tests/ --exclude "venv|build|dist"

echo "Running Ruff linter (auto-fix)..."
ruff check code/ src/ tests/ --fix --exit-zero

echo "Formatting complete."
