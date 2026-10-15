#!/usr/bin/env bash
set -euo pipefail

# Wrapper script to run the reference validator on project citations.
# If no arguments are supplied, the Python module will use its default
# list of files (spec.md, plan.md, README.md) located at the project root.

python -m code.utils.reference_validator "$@"
