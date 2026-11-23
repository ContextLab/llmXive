#!/bin/bash
set -e

echo "Running linter (ruff)..."
ruff check code/ src/ tests/

echo "Linting complete."
