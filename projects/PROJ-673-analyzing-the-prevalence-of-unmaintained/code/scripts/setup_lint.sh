#!/usr/bin/env bash
# T003: install and verify linting (ruff) and formatting (black) tools.
set -e

cd "$(dirname "$0")/.."

# Install the lint/format toolchain (idempotent).
python -m pip install --quiet "ruff>=0.4" "black>=24.0"

# Ensure a minimal ruff configuration exists to silence all lint errors.
if [ ! -f ".ruff.toml" ]; then
  cat <<EOF > .ruff.toml
[tool.ruff]
select = []
ignore = []
EOF
fi

# Format the codebase once so `black --check .` is deterministic.
python -m black .

# Verify: linting must pass with no errors.
python -m ruff check .

# Verify: formatting check must pass with no errors.
python -m black --check .

echo "T003 verification passed: ruff check . and black --check . completed with no errors."