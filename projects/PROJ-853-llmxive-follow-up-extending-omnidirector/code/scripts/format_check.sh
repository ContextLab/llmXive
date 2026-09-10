#!/bin/bash
set -e
cd "$(dirname "$0")/.."
echo "Checking Black formatting compliance..."
python -m black --check code/
echo "Formatting check passed."
