#!/bin/bash
set -e

echo "Running linter (ruff)..."
ruff check code/ tests/

echo "Running formatter check (black)..."
black --check code/ tests/

echo "Linting and formatting checks passed."
