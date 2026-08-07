#!/bin/bash
# Script to verify pipeline runtime compliance (T120)
# Exits with code 0 if runtime is within limits, 1 otherwise.

set -e

echo "Starting runtime verification (T120)..."

python code/verify_runtime.py

exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo "Runtime verification PASSED."
else
    echo "Runtime verification FAILED."
fi

exit $exit_code