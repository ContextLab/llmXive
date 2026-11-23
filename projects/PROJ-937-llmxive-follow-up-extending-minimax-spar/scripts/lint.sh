#!/bin/bash
# Lint code with Ruff
set -e
echo "Linting code with Ruff..."
ruff check code/ tests/
echo "Linting complete."
