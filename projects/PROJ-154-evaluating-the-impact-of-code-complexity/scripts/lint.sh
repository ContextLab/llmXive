#!/bin/bash
# Lint code with Ruff
set -e
echo "Running Ruff Lint..."
ruff check code/ tests/
echo "Linting complete."
