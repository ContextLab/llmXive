#!/usr/bin/env bash
set -euo pipefail

# Activate a local virtual environment if it exists.
if [ -f ".venv/bin/activate" ]; then
    source ".venv/bin/activate"
fi

# Ensure the project root is on PYTHONPATH so that `src` can be imported.
export PYTHONPATH="${PYTHONPATH}:$(pwd)"