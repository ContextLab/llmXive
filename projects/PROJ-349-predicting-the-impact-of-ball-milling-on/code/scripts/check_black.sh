#!/usr/bin/env bash
# ------------------------------------------------------------
# Script: check_black.sh
# Purpose: Verify that Black can read the project's pyproject.toml
#          configuration and that the codebase conforms to it.
# ------------------------------------------------------------
set -e  # Exit immediately if a command exits with a non-zero status.

# Use the module entrypoint to ensure Black is invoked from the
# project virtual environment, even if the `black` CLI is not on PATH.
python -m black --check .

# If we reach this point, Black succeeded.
echo "Black formatting check passed."