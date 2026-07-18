#!/bin/bash
# Run linter (ruff) and formatter check (black)

set -e

echo "Running ruff check..."
ruff check code/ tests/

echo "Running ruff format check..."
ruff format --check code/ tests/

echo "Linting and formatting checks passed."
