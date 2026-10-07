#!/bin/bash
# Run linters on the project
set -e

echo "Running Ruff linter..."
ruff check code/ tests/

echo "Running Black (check mode)..."
black --check code/ tests/

echo "Linting complete."
