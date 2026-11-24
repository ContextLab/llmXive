#!/usr/bin/env bash
set -euo pipefail

# Activate a local virtual environment if it exists.
if [ -f ".venv/bin/activate" ]; then
    source ".venv/bin/activate"
fi

# Ensure the 'code' directory is at the front of PYTHONPATH.
# This allows 'import src.pipeline' to resolve to 'code/src/pipeline'
# and avoids collisions with any top-level 'src' directories.
export PYTHONPATH="$(pwd)/code:${PYTHONPATH}"
