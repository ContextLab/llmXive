#!/usr/bin/env bash
set -euo pipefail

echo "Running Black and isort..."
python -m black code/ tests/
python -m isort code/ tests/
echo "Formatting complete."
