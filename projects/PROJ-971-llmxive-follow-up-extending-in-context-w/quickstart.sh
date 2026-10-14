#!/usr/bin/env bash
set -e

# Activate the virtual environment if it exists
if [ -f ".venv/bin/activate" ]; then
  source ".venv/bin/activate"
fi
