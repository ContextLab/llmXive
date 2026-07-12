#!/bin/bash
# Apply black formatting and isort to the project

set -e

echo "Running isort..."
isort code/

echo "Running black formatting..."
black code/

echo "Formatting applied successfully!"
