#!/usr/bin/env bash
set -euo pipefail

echo "Checking code style and linting..."
ruff check code/
black --check code/

echo "Lint check passed."