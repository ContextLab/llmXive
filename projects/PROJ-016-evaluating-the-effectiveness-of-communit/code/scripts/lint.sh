#!/bin/bash
# Run ruff linter and formatter checks
set -e

echo "Running ruff check..."
ruff check code/

echo "Running black check (dry-run)..."
black --check code/

echo "Linting and formatting checks passed."
