#!/bin/bash
# T001b: Initialize Python virtual environment
# This script creates a virtual environment using python3.11 and verifies activation.
# It must run in a single bash session to persist activation for subsequent checks.

set -e

# Ensure we are in the code directory
cd "$(dirname "$0")"

echo "Initializing Python virtual environment (T001b)..."

# Check for python3.11
if ! command -v python3.11 &> /dev/null; then
    echo "ERROR: python3.11 is not installed or not in PATH."
    exit 1
fi

# Remove existing venv if present to ensure a clean state
if [ -d ".venv" ]; then
    echo "Removing existing .venv directory..."
    rm -rf .venv
fi

# Create the virtual environment
echo "Creating virtual environment with python3.11..."
python3.11 -m venv .venv

# Activate and verify in a single subshell to simulate the requirement
# The task description implies the verification command runs in the same session.
# We use a subshell to capture the version output as proof of activation.
bash -c '
    source .venv/bin/activate &&
    echo "Virtual environment activated successfully." &&
    echo "Python version: $(python --version)" &&
    # Verify pip is available and working
    pip --version > /dev/null &&
    echo "Pip is available."
'

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to activate or verify the virtual environment."
    exit 1
fi

echo "T001b: Python virtual environment initialization completed successfully."
exit 0
