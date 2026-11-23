#!/bin/bash
set -e

echo "Running Ruff linter..."
ruff check code/ tests/

echo "Running Black check (diff only)..."
black --check code/ tests/

echo "Linting and format check complete."