#!/usr/bin/env bash
set -e

echo "Running Ruff linter..."
ruff check code/ tests/

echo "Running Black check (dry-run)..."
black --check code/ tests/

echo "Linting complete."
