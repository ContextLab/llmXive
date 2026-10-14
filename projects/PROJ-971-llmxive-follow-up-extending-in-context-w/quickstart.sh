#!/usr/bin/env bash
# Environment preparation for the Auto-ICWM quickstart.
# Sourced by CI via: bash -c "source quickstart.sh && ./run_minimal.sh"
# Activates the project virtual-env if one exists; otherwise the current
# Python environment (which already provides all dependencies) is used.
set -e
cd "$(dirname "${BASH_SOURCE[0]}")"
if [ -f .venv/bin/activate ]; then
    # shellcheck disable=SC1091
    source .venv/bin/activate
fi
export PYTHONPATH="${PWD}:${PYTHONPATH:-}"
export PYTHONHASHSEED=0
