#!/bin/bash
set -e

echo "Running linter (ruff)..."
ruff check .

echo "Linting complete."
