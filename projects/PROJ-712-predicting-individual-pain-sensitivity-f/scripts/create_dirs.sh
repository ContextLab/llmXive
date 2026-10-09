#!/usr/bin/env bash
# ------------------------------------------------------------
# create_dirs.sh
# ------------------------------------------------------------
# This script creates the required project directory hierarchy.
# It is used by CI to verify that the expected folders exist.
#
# Required directories:
#   data/raw
#   data/processed
#   artifacts
#   state
#   code
#   tests
#
# The script exits with status 0 on success and aborts on any error.
# ------------------------------------------------------------
set -euo pipefail

mkdir -p data/raw data/processed artifacts state code tests

echo "Directory structure created successfully."