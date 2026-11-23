#!/bin/bash
# Quick verification script to ensure mafft and fasttree are available
# This is intended to be run after setup_system_deps.py or manually

set -e

echo "Verifying system dependencies..."

if ! command -v mafft &> /dev/null; then
    echo "Error: mafft is not installed or not in PATH."
    exit 1
fi
echo "✓ mafft found: $(which mafft)"

if ! command -v FastTree &> /dev/null; then
    echo "Error: FastTree is not installed or not in PATH."
    exit 1
fi
echo "✓ FastTree found: $(which FastTree)"

echo "All dependencies verified successfully."