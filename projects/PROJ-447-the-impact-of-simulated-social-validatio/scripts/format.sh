#!/bin/bash
# Format code with Black and sort imports with Ruff

echo "Running Black formatter..."
black code/ tests/

echo "Running Ruff linter (fix mode)..."
ruff check --fix code/ tests/

echo "Formatting complete."
