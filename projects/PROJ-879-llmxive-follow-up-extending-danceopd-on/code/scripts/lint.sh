#!/bin/bash
set -e

echo "Running Ruff Linter..."
ruff check .

echo "Running Black Formatter Check..."
black --check .

echo "Linting and formatting checks passed."
