#!/bin/bash
set -e
echo "Running linter (ruff)..."
ruff check code/src/ code/tests/ code/scripts/
echo "Linting complete."