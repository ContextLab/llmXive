#!/usr/bin/env bash
# Setup linting: run ruff and black, capture their output in logs/lint.txt

set -e

# Ensure the logs directory exists
LOG_DIR="logs"
mkdir -p "$LOG_DIR"

# Run ruff and black, capture both stdout and stderr
{
    echo "=== ruff check ==="
    ruff check .
    echo "=== black --check ==="
    black --check .
} > "$LOG_DIR/lint.txt" 2>&1

echo "Linting completed. Output written to $LOG_DIR/lint.txt"