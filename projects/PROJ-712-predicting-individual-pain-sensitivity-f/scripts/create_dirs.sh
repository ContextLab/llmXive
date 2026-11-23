#!/usr/bin/env bash
# ------------------------------------------------------------
# create_dirs.sh
# ------------------------------------------------------------
# Creates the required project-owned directory hierarchy.
# Used by CI (tests/integration/test_structure.py) to verify that
# the expected folders exist after this script exits with code 0.
#
# Required directories (all six, per task T001):
#   data/raw
#   data/processed
#   artifacts
#   code
#   tests
#   scripts
#
# Note: 'state/' is platform-owned and must NOT be created here.
# The script exits with status 0 on success and aborts on any error.
# ------------------------------------------------------------
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

mkdir -p data/raw data/processed artifacts code tests scripts

echo "Directory structure created successfully."
