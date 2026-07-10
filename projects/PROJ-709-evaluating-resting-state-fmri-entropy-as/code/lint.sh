#!/bin/bash
# Run linting checks using Ruff
set -e

echo "Running Ruff linter..."
ruff check code/

echo "Running Black check (dry-run)..."
black --check code/

echo "Linting complete."