#!/usr/bin/env bash
# T001: create the required project layout (including data/results/ with a
# placeholder), format the codebase, and record lint evidence in logs/lint.txt.
set -euo pipefail
cd "$(dirname "$0")/.."

# ------------------------------------------------------------------
# 1. Required directory layout (per plan.md project structure)
# ------------------------------------------------------------------
mkdir -p data/raw data/processed data/results/fork_points \
         data/results/validation data/results/report logs

# Placeholder files so the (empty) directories are tracked
touch data/raw/.gitkeep
touch data/processed/.gitkeep
touch data/results/.gitkeep

echo "Project layout created:"
find data logs -type d | sort

# ------------------------------------------------------------------
# 2. Ensure linting tools are available
# ------------------------------------------------------------------
if ! python -m ruff --version >/dev/null 2>&1; then
  python -m pip install --quiet ruff
fi
if ! python -m black --version >/dev/null 2>&1; then
  python -m pip install --quiet black
fi

# ------------------------------------------------------------------
# 3. Format once so the tree is black-clean, then record evidence
# ------------------------------------------------------------------
python -m black .

{
  echo "=== ruff check . ==="
  python -m ruff check .
  echo "ruff exit code: $?"
  echo
  echo "=== black --check . ==="
  python -m black --check .
  echo "black exit code: $?"
} > logs/lint.txt 2>&1

cat logs/lint.txt
echo "Lint evidence written to logs/lint.txt"
