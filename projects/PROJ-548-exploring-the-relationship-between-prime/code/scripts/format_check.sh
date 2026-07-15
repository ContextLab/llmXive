#!/usr/bin/env bash
set -euo pipefail

echo "Checking code formatting with Black..."
black --check code/ tests/

echo "Checking formatting complete."
