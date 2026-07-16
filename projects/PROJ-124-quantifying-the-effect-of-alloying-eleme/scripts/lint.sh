#!/bin/bash
# Run linters without fixing

set -e

echo "Running Ruff linter..."
ruff check code/ tests/

echo "Running Black check (no write)..."
black --check code/ tests/

echo "Linting complete!"
