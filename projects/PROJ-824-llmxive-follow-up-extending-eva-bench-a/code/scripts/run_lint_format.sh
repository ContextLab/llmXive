#!/bin/bash
# Convenience script to run linting and formatting checks on the codebase.

set -e

echo "Running Black format check..."
black --check code/

echo "Running Ruff lint check..."
ruff check code/

echo "All checks passed!"
