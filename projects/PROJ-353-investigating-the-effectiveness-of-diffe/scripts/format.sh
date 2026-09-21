#!/bin/bash
set -e

echo "Running isort..."
isort code/ tests/

echo "Running black..."
black code/ tests/

echo "Formatting complete."