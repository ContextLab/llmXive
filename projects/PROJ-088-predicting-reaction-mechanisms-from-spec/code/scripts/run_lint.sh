#!/bin/bash
set -e

echo "Running Ruff Linter..."
ruff check code/

echo "Running Ruff Formatter Check..."
ruff format --check code/

echo "Linting complete."
