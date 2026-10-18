#!/usr/bin/env bash
# ------------------------------------------------------------
# Linting helper script for the project.
# Executes ruff and black in check mode and writes the combined
# output to logs/lint.txt. Both tools must exit with code 0.
# ------------------------------------------------------------
set -euo pipefail

# Ensure the logs directory exists
mkdir -p logs

# Run ruff and black, capturing stdout and stderr.
{
    echo "=== ruff check ==="
    ruff check .
    echo "=== black --check ==="
    black --check .
} > logs/lint.txt 2>&1

echo "Linting completed successfully. Output written to logs/lint.txt"
