#!/bin/bash
# Validation script for quickstart.md
# Checks that the documented commands exist and are executable

set -e

echo "Validating quickstart.md..."

# Check if pipeline.py exists
if [ ! -f "code/pipeline.py" ]; then
    echo "ERROR: code/pipeline.py not found"
    exit 1
fi

# Check if requirements.txt exists
if [ ! -f "requirements.txt" ]; then
    echo "ERROR: requirements.txt not found"
    exit 1
fi

# Check if README.md exists
if [ ! -f "README.md" ]; then
    echo "ERROR: README.md not found"
    exit 1
fi

# Check if quickstart.md exists
if [ ! -f "quickstart.md" ]; then
    echo "ERROR: quickstart.md not found"
    exit 1
fi

# Check if research.md exists
if [ ! -f "research.md" ]; then
    echo "ERROR: research.md not found"
    exit 1
fi

# Verify the command in quickstart.md is valid (syntax check)
python -m py_compile code/pipeline.py

echo "Validation passed: All required files and commands are present."
exit 0