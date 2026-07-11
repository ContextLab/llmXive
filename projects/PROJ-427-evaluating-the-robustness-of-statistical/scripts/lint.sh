#!/bin/bash
set -e

echo "Running Ruff Linter..."
ruff check code/ tests/

echo "Running Ruff Formatter Check..."
ruff format --check code/ tests/

echo "Linting complete."
