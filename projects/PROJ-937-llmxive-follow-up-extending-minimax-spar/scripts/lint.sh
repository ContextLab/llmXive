#!/bin/bash
# Run linters without auto-fixing
set -e

echo "Running Ruff linter..."
ruff check code/ tests/

echo "Running Black check (dry-run)..."
black --check code/ tests/

echo "Linting complete."
