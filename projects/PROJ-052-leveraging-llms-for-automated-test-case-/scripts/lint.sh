#!/usr/bin/env bash
# Lint and format the project's Python code (Task T003).
# Usage:
#   bash scripts/lint.sh          # check only (ruff check + black --check)
#   bash scripts/lint.sh --fix    # auto-fix (ruff --fix + black)
set -euo pipefail

MODE="${1:-check}"

if ! command -v ruff >/dev/null 2>&1; then
    echo "ERROR: ruff is not installed. Run: pip install ruff==0.4.4" >&2
    exit 1
fi
if ! command -v black >/dev/null 2>&1; then
    echo "ERROR: black is not installed. Run: pip install black==24.4.2" >&2
    exit 1
fi

TARGETS=(code/ tests/)

if [ "$MODE" = "--fix" ]; then
    echo "Running ruff --fix ..."
    ruff check --fix "${TARGETS[@]}"
    echo "Running black (formatting) ..."
    black "${TARGETS[@]}"
else
    echo "Running ruff check ..."
    ruff check "${TARGETS[@]}"
    echo "Running black --check ..."
    black --check "${TARGETS[@]}"
fi

echo "Lint/format ($MODE) completed successfully."
