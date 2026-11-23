#!/bin/bash
# T008b: Pipeline Orchestrator and Environment Verifier
# This script orchestrates the pipeline: imports modules, runs T008a test,
# and exits with code 1 on failure.

set -e

echo "Starting Environment Verification for PROJ-727..."

# Change to project root to ensure relative paths work
# Assuming the script is run from the project root or we adjust accordingly.
# The task requires running the test.

# 1. Run the T008a dummy test to verify environment without OOM risk.
# The test is located at tests/test_dummy.py and the function is test_dummy_inference.
echo "Running T008a: test_dummy_inference..."
python -m pytest tests/test_dummy.py::test_dummy_inference -v

if [ $? -ne 0 ]; then
    echo "ERROR: T008a test failed. Environment verification unsuccessful."
    exit 1
fi

echo "T008a test passed."
echo "Environment Verified."
exit 0