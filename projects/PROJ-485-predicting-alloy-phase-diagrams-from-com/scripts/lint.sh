#!/bin/bash
# Run linter and formatter checks
set -e

echo "Running Black formatter check..."
black --check --diff code/ tests/

echo "Running Ruff linter..."
ruff check code/ tests/

echo "Linting and formatting checks passed."
