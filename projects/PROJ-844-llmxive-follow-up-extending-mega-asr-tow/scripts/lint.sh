#!/bin/bash
# Script to check code style and linting (no autofix)

set -e

echo "Running Black check (dry-run)..."
black --check code/ tests/

echo "Running Ruff check..."
ruff check code/ tests/

echo "Linting complete."