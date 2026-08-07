#!/bin/bash
# T125: Execute stability verification script
# Depends on T119 (stability check execution) and T109 (stability verification logic)
# This script runs the stability check and then verifies the results.

set -e

echo "=== T125: Stability Verification Execution ==="

# Ensure we are in the project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

echo "Project root: $PROJECT_ROOT"

# 1. Run the stability check script (T109 dependency)
echo "Running stability check (scripts/stability_check.sh)..."
if [ -f "scripts/stability_check.sh" ]; then
    chmod +x scripts/stability_check.sh
    scripts/stability_check.sh
else
    echo "ERROR: scripts/stability_check.sh not found."
    exit 1
fi

# 2. Run the stability verifier script (T109 dependency)
echo "Running stability verifier (scripts/stability_verify.sh)..."
if [ -f "scripts/stability_verify.sh" ]; then
    chmod +x scripts/stability_verify.sh
    scripts/stability_verify.sh
    VERIFIER_EXIT_CODE=$?
else
    echo "ERROR: scripts/stability_verify.sh not found."
    exit 1
fi

# 3. Final Status
if [ $VERIFIER_EXIT_CODE -eq 0 ]; then
    echo "SUCCESS: Stability criterion (rank-difference <= 1) is met."
    echo "T125 verification passed."
    exit 0
else
    echo "FAILURE: Stability criterion not met."
    echo "T125 verification failed."
    exit 1
fi