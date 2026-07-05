#!/bin/bash
# Check if code is formatted correctly without modifying

set -e

echo "Checking code formatting..."
black --check code/ tests/ || {
    echo "Formatting check failed. Run 'black code/ tests/' to fix."
    exit 1
}

echo "Formatting check passed."
