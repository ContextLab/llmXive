#!/usr/bin/env bash
# Lint and format-check entry point for the decoding-internal-states pipeline.
# Usage (from repository root):   bash code/lint.sh
# Usage (from code/ directory):   bash lint.sh
# Exits non-zero if any tool is missing or any check fails.
set -euo pipefail

# Resolve the code/ directory regardless of where the script is invoked from.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Verify tool availability — fail loudly rather than silently skipping.
for tool in flake8 black; do
    if ! python -m "$tool" --version >/dev/null 2>&1; then
        echo "ERROR: required lint tool '$tool' is not installed." >&2
        echo "Install it with: pip install flake8 black" >&2
        exit 1
    fi
done

echo "=== flake8 (config: code/.flake8) ==="
python -m flake8 .

echo "=== black --check (config: code/pyproject.toml) ==="
python -m black --check .

echo "All lint and format checks passed."
