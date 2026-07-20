#!/bin/bash
# Linting script for Socratic Transformers project
# Runs ruff check and black --check on all Python files in src/ and tests/

set -e

echo "Running Ruff check..."
ruff check src/ tests/

echo "Running Black check..."
black --check src/ tests/

echo "Linting complete. All checks passed."
