#!/bin/bash
set -e

echo "Formatting code with black and isort..."
python -m isort code/ tests/
python -m black code/ tests/

echo "Formatting complete."