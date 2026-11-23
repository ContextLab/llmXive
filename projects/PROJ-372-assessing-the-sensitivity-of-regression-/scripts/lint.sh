#!/bin/bash
set -e

echo "Running Ruff linter..."
ruff check src/ tests/

echo "Linting complete."
