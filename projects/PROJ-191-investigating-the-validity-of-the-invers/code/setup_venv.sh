#!/usr/bin/env bash
# T002-A: Initialize the project virtual environment.
# Creates `venv/` at the project root and verifies venv/bin/activate exists.
# Constraint: ensure a compatible Python version; fall back to python3.11
# if the default interpreter is too old.
set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

# Helper: is the given interpreter compatible (>= 3.9)?
version_ok () {
    "$1" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)' 2>/dev/null
}

# Choose a compatible interpreter.
PY=python
if ! version_ok "$PY"; then
    echo "Default python is not compatible; trying python3.11..."
    if command -v python3.11 >/dev/null 2>&1 && version_ok python3.11; then
        PY=python3.11
    else
        echo "ERROR: no compatible Python (>= 3.9, or python3.11) found on PATH." >&2
        exit 1
    fi
fi

echo "Using interpreter: $($PY --version)"

# Create the virtual environment at the project root (idempotent).
if [ -f "venv/bin/activate" ]; then
    echo "venv already exists; recreating to guarantee a clean, compatible environment."
    rm -rf venv
fi
"$PY" -m venv venv

# Verify venv/bin/activate exists.
if [ ! -f "venv/bin/activate" ]; then
    echo "ERROR: venv/bin/activate was not created." >&2
    exit 1
fi
echo "Verified: venv/bin/activate exists."

# Report the venv's Python version.
"venv/bin/python" --version
"venv/bin/python" -c 'import sys; assert sys.version_info >= (3, 9), "venv Python is incompatible"; print("venv Python version is compatible.")'

echo "T002-A complete: virtual environment initialized at $PROJECT_ROOT/venv"