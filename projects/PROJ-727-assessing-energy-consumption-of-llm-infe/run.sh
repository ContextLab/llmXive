#!/bin/bash
# T008: Environment Verification Entry Point
# This script verifies the environment by running the dummy inference test.
# It exits with code 1 on failure and code 0 on success.

set -e

echo "Starting environment verification..."

# Run the dummy inference test
# This test performs a lightweight import check and a single-token generation
# using a tiny model to verify the environment without OOM risk.
python -m pytest tests/test_dummy.py::test_dummy_inference -v

if [ $? -eq 0 ]; then
    echo "Environment Verified"
    exit 0
else
    echo "Environment verification failed."
    exit 1
fi