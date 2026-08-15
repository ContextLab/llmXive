#!/bin/bash
set -e
echo "Running Ruff linter..."
ruff check code/
echo "Running Ruff formatter (black compatible)..."
ruff format --check code/
echo "Linting and formatting check passed."
