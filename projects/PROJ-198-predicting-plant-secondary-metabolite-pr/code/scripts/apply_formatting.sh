#!/bin/bash
set -e

echo "Step 1: Running Ruff to fix linting and imports..."
# 'ruff check --fix' handles linting and 'I' (isort)
# This must run before Black because Ruff may change line structures
ruff check --fix .

echo "Step 2: Running Black to format code..."
# Black is the final authority on formatting
black .

echo "Step 3: Verifying Ruff (no remaining fixable errors)..."
# Verify that no new linting errors were introduced and no fixables remain
ruff check .

echo "Step 4: Verifying Black (no formatting changes needed)..."
# Final check to ensure codebase is 100% Black-compliant
black --check .

echo "Linting and formatting verification successful."