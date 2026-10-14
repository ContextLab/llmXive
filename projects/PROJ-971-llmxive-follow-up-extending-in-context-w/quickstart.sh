#!/usr/bin/env bash
# Prepare the environment for the minimal Auto-ICWM pipeline.
# Activates the project virtual-env if one exists; otherwise relies on
# the ambient Python environment.
set -e
if [ -f .venv/bin/activate ]; then
    source .venv/bin/activate
fi
echo "quickstart: environment ready"
