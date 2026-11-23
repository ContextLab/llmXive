#!/bin/bash
# Lint code with Ruff
set -e

echo "Running Ruff check..."
ruff check code/ tests/

echo "Linting complete."