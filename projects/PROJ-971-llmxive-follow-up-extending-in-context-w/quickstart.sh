#!/usr/bin/env bash
# Quickstart helper – activate virtual environment (if present) and set PYTHONPATH.
set -e
if [ -f ".venv/bin/activate" ]; then
  source .venv/bin/activate
fi
export PYTHONPATH="$(pwd):$PYTHONPATH"
