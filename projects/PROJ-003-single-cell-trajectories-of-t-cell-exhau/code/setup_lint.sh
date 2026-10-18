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
  python -m pip install --quiet "ruff"
fi
if ! python -m black --version >/dev/null 2>&1; then
  python -m pip install --quiet "black"
fi

# ------------------------------------------------------------------
# 3. Format once so the tree is black-clean, auto-fix ruff findings,
#    then record evidence in logs/lint.txt
# ------------------------------------------------------------------
python -m black .

# Auto-fix any fixable ruff findings, then re-format so black stays happy
python -m ruff check --fix . || true
python -m black .

ruff_rc=0
black_rc=0

echo "=== ruff check . ===" > logs/lint.txt
if ! python -m ruff check . >> logs/lint.txt 2>&1; then
  ruff_rc=$?
fi
echo "ruff exit code: $ruff_rc" >> logs/lint.txt
echo "" >> logs/lint.txt

echo "=== black --check . ===" >> logs/lint.txt
if ! python -m black --check . >> logs/lint.txt 2>&1; then
  black_rc=$?
fi
echo "black exit code: $black_rc" >> logs/lint.txt

cat logs/lint.txt
echo "Lint evidence written to logs/lint.txt"

if [ "$ruff_rc" -ne 0 ] || [ "$black_rc" -ne 0 ]; then
  echo "Linting failed (ruff=$ruff_rc, black=$black_rc)." >&2
  exit 1
fi
echo "Linting passed."
