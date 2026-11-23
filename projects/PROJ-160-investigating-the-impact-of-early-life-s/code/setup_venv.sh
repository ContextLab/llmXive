#!/usr/bin/env bash
# T002b: Install dependencies from requirements.txt into an isolated
# virtualenv at <project>/.venv and verify all packages are present.
set -euo pipefail

# Resolve project root (two levels above this script: code/setup_venv.sh)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

REQUIREMENTS="$PROJECT_ROOT/requirements.txt"
VENV_DIR="$PROJECT_ROOT/.venv"
LOG_DIR="$PROJECT_ROOT/logs"
mkdir -p "$LOG_DIR"
VERIFY_LOG="$LOG_DIR/dependency_verification.txt"

if [ ! -f "$REQUIREMENTS" ]; then
    echo "ERROR: requirements.txt not found at $REQUIREMENTS" >&2
    exit 1
fi

echo "Creating isolated virtualenv at $VENV_DIR ..."
python -m venv "$VENV_DIR"

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

echo "Upgrading pip ..."
python -m pip install --quiet --upgrade pip

echo "Installing dependencies from $REQUIREMENTS ..."
python -m pip install -r "$REQUIREMENTS"

echo "Installed packages (python -m pip list):"
python -m pip list | tee "$VERIFY_LOG"

# Verify every requirement name is present in the installed package list
MISSING=0
while IFS= read -r line; do
    # Strip comments and whitespace; skip empty lines and options
    line="$(echo "$line" | sed -e 's/#.*//' -e 's/[[:space:]]*$//' -e 's/^[[:space:]]*//')"
    [ -z "$line" ] && continue
    case "$line" in
        -*) continue ;;
    esac
    # Extract package name (strip version specifiers and extras)
    pkg="$(echo "$line" | sed -e 's/[=<>!~;[].*//' -e 's/[[:space:]]*$//')"
    if ! python -m pip show "$pkg" > /dev/null 2>&1; then
        echo "MISSING PACKAGE: $pkg" | tee -a "$VERIFY_LOG"
        MISSING=1
    fi
done < "$REQUIREMENTS"

if [ "$MISSING" -ne 0 ]; then
    echo "ERROR: one or more required packages are missing." | tee -a "$VERIFY_LOG"
    exit 1
fi

echo "All required packages are installed in $VENV_DIR." | tee -a "$VERIFY_LOG"
echo "Verification log written to $VERIFY_LOG"
deactivate