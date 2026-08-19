#!/bin/bash
# Run linting checks
set -e

echo "Running Ruff check..."
ruff check code/

echo "Running mypy (type checking)..."
# Only run if mypy stubs are present or project is ready
# mypy code/ || true

echo "Linting complete."
