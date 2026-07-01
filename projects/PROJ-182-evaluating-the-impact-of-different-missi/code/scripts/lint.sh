#!/bin/bash
# Script to check code style and linting without modifying files
set -e

echo "Running Black check (no write)..."
black --check code/src code/tests

echo "Running Ruff check..."
ruff check code/src code/tests

echo "Linting complete."