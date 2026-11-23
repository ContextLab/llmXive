#!/bin/bash
# Script to run graph validation for T018
# Validates code/data/processed/graphs.parquet against code/contracts/dataset_graph.schema.yaml

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Running Graph Validation (Task T018)..."
echo "Project Root: $PROJECT_ROOT"

cd "$PROJECT_ROOT"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Run the validation script
echo "Executing validation..."
python src/data/validate_graphs.py

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "Validation completed successfully."
elif [ $EXIT_CODE -eq 1 ]; then
    echo "Validation failed: Some graphs are invalid."
else
    echo "Validation failed with critical error."
fi

exit $EXIT_CODE
