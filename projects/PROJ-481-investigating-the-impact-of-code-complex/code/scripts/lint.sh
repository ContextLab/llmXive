#!/bin/bash
set -e

echo "Running Ruff linter..."
ruff check .

echo "Linting complete."
