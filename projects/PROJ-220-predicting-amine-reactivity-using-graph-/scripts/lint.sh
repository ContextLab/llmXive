#!/usr/bin/env bash
# Script to run linting checks using Ruff
set -e

echo "Running Ruff linting..."
ruff check src/ tests/

echo "Linting complete."
