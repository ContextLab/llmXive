#!/usr/bin/env bash
set -euo pipefail

echo "Checking code with Ruff..."
ruff check code/ tests/

echo "Lint check complete."
