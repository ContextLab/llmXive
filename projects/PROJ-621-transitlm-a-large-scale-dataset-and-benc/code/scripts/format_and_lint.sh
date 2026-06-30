#!/bin/bash
set -e

echo "Running Black formatter..."
black code/

echo "Running Ruff linter..."
ruff check code/

echo "Linting and formatting complete."
