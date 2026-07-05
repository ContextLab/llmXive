#!/bin/bash
set -e

echo "Running isort..."
isort code/

echo "Running black..."
black code/

echo "Formatting complete."