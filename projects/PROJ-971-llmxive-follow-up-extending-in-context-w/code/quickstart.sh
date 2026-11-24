#!/usr/bin/env bash
#
# quickstart.sh – prepare environment for the minimal pipeline.
#
# If a local virtual environment exists in .venv, activate it.
# Also ensure the project root is on PYTHONPATH so that `src` can be imported.
#
set -e

# Activate .venv if present
if [ -d ".venv" ]; then
    # shellcheck disable=SC1091
    source .venv/bin/activate
fi

# Ensure the project root is on PYTHONPATH
export PYTHONPATH="$(pwd):${PYTHONPATH}"
