#!/usr/bin/env bash
# ------------------------------------------------------------
# run_test_structure.sh
# ------------------------------------------------------------
# Executes the integration test that validates the directory
# creation script and writes the JUnit XML report to
# artifacts/test_structure.xml.
# ------------------------------------------------------------
set -euo pipefail

# Resolve project root (script resides in scripts/)
cd "$(dirname "${BASH_SOURCE[0]}")/.."

# Ensure the artifacts directory exists
mkdir -p artifacts

# Run the test and capture JUnit output
pytest -q tests/integration/test_structure.py --junitxml=artifacts/test_structure.xml
