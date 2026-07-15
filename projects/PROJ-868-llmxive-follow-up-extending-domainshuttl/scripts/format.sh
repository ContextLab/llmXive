#!/bin/bash
set -e

echo "Running Black formatter..."
black src/ tests/ scripts/

echo "Running Ruff linter (fix mode)..."
ruff check --fix src/ tests/ scripts/

echo "Running Ruff formatter (if available, else skip)..."
if ruff format --check src/ tests/ scripts/ > /dev/null 2>&1; then
    ruff format src/ tests/ scripts/
else
    echo "Ruff format not available or not needed. Using Black."
fi

echo "Formatting complete."
