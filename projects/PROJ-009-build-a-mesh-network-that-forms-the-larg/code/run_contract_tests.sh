#!/usr/bin/env bash
set -euo pipefail

# Ensure the logs directory exists
LOG_DIR="logs"
mkdir -p "${LOG_DIR}"

# Run the contract test suite and capture output
pytest code/tests/contract/ -q > "${LOG_DIR}/pytest_contracts.log"

# Exit with pytest's exit code (0 means all tests passed)
exit "${PIPESTATUS[0]}"