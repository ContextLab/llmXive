#!/bin/bash
set -e

echo "Running linter (ruff)..."
ruff check code/ tests/

echo "Linting complete."
