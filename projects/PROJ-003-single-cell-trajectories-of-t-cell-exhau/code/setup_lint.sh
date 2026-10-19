#!/usr/bin/env bash
# ----------------------------------------------------------------------
# Run ruff and black in check mode, capture their output, and store it
# in logs/lint.txt. The script exits on any error (set -e) so the CI
# will fail if either tool returns a non‑zero status.
# ----------------------------------------------------------------------
set -e

LOG_DIR="logs"
mkdir -p "$LOG_DIR"

{
    echo "=== ruff check ==="
    ruff check .
    echo "=== black --check ==="
    black --check .
} > "$LOG_DIR/lint.txt"
