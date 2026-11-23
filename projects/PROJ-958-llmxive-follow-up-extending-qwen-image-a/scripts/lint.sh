#!/bin/bash
# Lint code with Ruff only (no auto-fix)
set -e

echo "Running Ruff check..."
ruff check src/ tests/ --exclude "data/"

echo "Linting complete."