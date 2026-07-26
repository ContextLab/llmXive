#!/bin/bash
# setup.sh - Automated directory creation and verification script for llmXive project
# This script ensures the project structure is correctly initialized.

set -e  # Exit immediately if a command exits with a non-zero status

# Determine the project root (directory where this script is located)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ROOT_DIR="$SCRIPT_DIR"

echo "=== llmXive Project Setup ==="
echo "Project Root: $ROOT_DIR"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is required but not found."
    exit 1
fi

echo "Running directory creation and verification..."

# Run the Python setup script
# We use python3 explicitly to ensure compatibility
python3 -c "
import sys
import os
from pathlib import Path

# Add the code directory to the path if the script is run from root
# This assumes setup_project.py is in the root or code/ depending on structure
# Based on API surface, setup_project.py is in code/
code_dir = Path('$ROOT_DIR') / 'code'
if code_dir.exists():
    sys.path.insert(0, str(code_dir))

try:
    from setup_project import create_directories, verify_directories
except ImportError as e:
    print(f'Error importing setup_project: {e}')
    print('Ensure code/setup_project.py exists.')
    sys.exit(1)

root_path = Path('$ROOT_DIR')

# Create directories
print('Creating directories...')
created = create_directories(root_path)
if created:
    for d in created:
        print(f'  Created: {d}')
else:
    print('  All directories already exist.')

# Verify directories
print('Verifying directories...')
if verify_directories(root_path):
    print('Setup completed successfully.')
    sys.exit(0)
else:
    print('Setup verification failed.')
    sys.exit(1)
"

exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo ""
    echo "=== Directory Structure ==="
    echo "code/"
    echo "data/"
    echo "  raw/"
    echo "  processed/"
    echo "  reports/"
    echo "tests/"
    echo "state/"
    echo "=========================="
else
    echo "Setup failed with exit code $exit_code"
fi

exit $exit_code
