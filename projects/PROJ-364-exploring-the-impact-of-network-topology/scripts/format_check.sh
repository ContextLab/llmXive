#!/bin/bash
# Check formatting without modifying files

set -e

echo "Checking Black formatting..."
black --check .

echo "Format check complete."