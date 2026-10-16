#!/usr/bin/env bash
# ------------------------------------------------------------
# Script: check_black.sh
# Purpose: Verify that Black can read the project's pyproject.toml
#          configuration and that the codebase conforms to it.
# ------------------------------------------------------------
set -e  # Exit immediately if a command exits with a non-zero status.

# Run Black in check mode on the repository root.
# The command will output the formatting status; any violations will
# cause a non‑zero exit code, which makes the task fail.
black --check .

# If we reach this point, Black succeeded.
echo "Black formatting check passed."