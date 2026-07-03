#!/bin/bash
set -e

echo "Running Black formatter..."
black code/ tests/

echo "Running Ruff linter (fixing where possible)..."
ruff check --fix code/ tests/

echo "Formatting complete."
