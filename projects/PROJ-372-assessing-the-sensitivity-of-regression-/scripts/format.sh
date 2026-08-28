#!/bin/bash
set -e

echo "Running Black formatter..."
black src/ tests/

echo "Running Ruff linter (check only)..."
ruff check src/ tests/

echo "Running Ruff formatter (if available)..."
ruff format src/ tests/ || echo "Ruff format not available, skipping."

echo "Formatting complete."
