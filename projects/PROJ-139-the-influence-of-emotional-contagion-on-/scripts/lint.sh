#!/bin/bash
# Lint code without auto-fixing

set -e

echo "Running Black check (dry run)..."
black --check code/

echo "Running Ruff check..."
ruff check code/

echo "Linting complete."
