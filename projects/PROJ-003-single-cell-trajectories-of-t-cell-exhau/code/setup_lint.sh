#!/usr/bin/env bash
set -euo pipefail

# ------------------------------------------------------------
# Project layout creation
# ------------------------------------------------------------
# Ensure required directories exist
mkdir -p data/results
mkdir -p logs

# Create placeholder file so the directory is non‑empty
touch data/results/.gitkeep

# ------------------------------------------------------------
# Linting
# ------------------------------------------------------------
# Run ruff and black, capture their output in logs/lint.txt.
# The script will exit with a non‑zero status if either tool reports errors,
# ensuring that the CI fails when linting is not clean.
LOG_FILE="logs/lint.txt"
{
  echo "=== ruff check ==="
  ruff check .
  echo "=== black --check ==="
  black --check .
  echo "=== Linting completed successfully ==="
} > "$LOG_FILE" 2>&1

echo "Lint log written to $LOG_FILE"