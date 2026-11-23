#!/bin/bash
# Script to run the directory setup process
# This ensures the project structure is created before other tasks run

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/.."

echo "Running directory setup..."
python scripts/setup_directories.py

echo "Verifying directory structure..."
python -m pytest tests/unit/test_directory_structure.py -v

echo "Setup verification complete."
