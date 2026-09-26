#!/usr/bin/env bash
# Lint codebase using ruff
set -e

echo "Running ruff check..."
python -m ruff check code/ tests/

echo "Running ruff format check..."
python -m ruff format --check code/ tests/

echo "Linting complete."
