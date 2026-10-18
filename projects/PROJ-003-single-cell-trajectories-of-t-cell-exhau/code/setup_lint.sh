#!/usr/bin/env bash
# One-time setup: create the required project layout (including
# data/results/ with a .gitkeep placeholder), format the codebase with
# black, and record genuine lint evidence in logs/lint.txt.
#
# This script FAILS LOUDLY: if `ruff check .` or `black --check .`
# return a non-zero exit code, the script exits non-zero and the
# failure is visible in logs/lint.txt (no masking).
set -euo pipefail

cd "$(dirname "$0")/.."
PROJECT_ROOT="$(pwd)"
echo "Project root: ${PROJECT_ROOT}"

# ------------------------------------------------------------------
# 1. Required directory layout (T001)
# ------------------------------------------------------------------
mkdir -p data/raw \
         data/processed \
         data/results \
         data/results/fork_points \
         data/results/validation \
         data/results/report \
         logs \
         tests/unit \
         tests/integration

# Placeholder files so the (empty) directories are tracked
touch data/raw/.gitkeep
touch data/processed/.gitkeep
touch data/results/.gitkeep

# ------------------------------------------------------------------
# 2. Ensure linting tools are available
# ------------------------------------------------------------------
if ! python -m ruff --version >/dev/null 2>&1; then
    echo "ruff not found; installing..."
    python -m pip install --quiet ruff
fi
if ! python -m black --version >/dev/null 2>&1; then
    echo "black not found; installing..."
    python -m pip install --quiet black
fi

# ------------------------------------------------------------------
# 3. Format the codebase first so `black --check .` can genuinely pass
# ------------------------------------------------------------------
echo "Formatting codebase with black..."
python -m black .

# ------------------------------------------------------------------
# 4. Lint evidence -> logs/lint.txt (SC-001)
#    With `pipefail` set, a non-zero exit from ruff or black
#    propagates through `tee` and fails this script.
# ------------------------------------------------------------------
{
    echo "== ruff check . =="
    python -m ruff check .
    echo "ruff exit code: 0"
    echo ""
    echo "== black --check . =="
    python -m black --check .
    echo "black exit code: 0"
} 2>&1 | tee logs/lint.txt

echo ""
echo "Setup complete: layout created and lint evidence written to logs/lint.txt"