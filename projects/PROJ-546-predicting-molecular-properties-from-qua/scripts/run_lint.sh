#!/bin/bash
# Run linting checks using ruff
set -e

echo "Running ruff lint..."
ruff check code/ tests/

echo "Linting passed."
