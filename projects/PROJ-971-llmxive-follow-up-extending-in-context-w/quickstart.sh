#!/usr/bin/env bash
set -e
# Activate a virtual environment if it exists.
if [ -f ".venv/bin/activate" ]; then
  source .venv/bin/activate
fi
# Ensure the project root is on PYTHONPATH.
export PYTHONPATH="$(pwd)"
