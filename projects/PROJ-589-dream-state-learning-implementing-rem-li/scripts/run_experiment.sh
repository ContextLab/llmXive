#!/usr/bin/env bash
set -euo pipefail

# Wrapper script used by CI to invoke the multi‑seed experiment.
# It simply forwards to the Python orchestrator with its default arguments.
python code/main.py "$@"
