#!/bin/bash
set -e

echo "Running Ruff linter..."
ruff check code/ tests/

echo "Linting complete."
