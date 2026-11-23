#!/bin/bash
# Quickstart validation script for PROJ-174
# This script verifies the pipeline can run end-to-end and produces required artifacts.

set -e

echo "=== PROJ-174 Quickstart Validation ==="
echo "Starting validation at $(date)"

# Ensure we are in the project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

echo "Project root: $PROJECT_ROOT"

# 1. Verify directory structure
echo "Checking directory structure..."
if [ ! -d "code" ] || [ ! -d "data" ] || [ ! -d "results" ]; then
    echo "ERROR: Missing required directories (code, data, results)"
    exit 1
fi
echo "Directory structure OK."

# 2. Verify Python environment
echo "Checking Python environment..."
if [ -f "code/.venv/bin/python" ]; then
    PYTHON_CMD="code/.venv/bin/python"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
else
    echo "ERROR: No Python 3 found"
    exit 1
fi

$PYTHON_CMD --version
echo "Python environment OK."

# 3. Run the main pipeline
echo "Running main pipeline..."
cd code
$PYTHON_CMD main.py
PIPELINE_EXIT=$?
cd ..

if [ $PIPELINE_EXIT -ne 0 ]; then
    echo "ERROR: Pipeline execution failed with exit code $PIPELINE_EXIT"
    exit 1
fi
echo "Pipeline execution OK."

# 4. Verify required output artifacts
echo "Verifying output artifacts..."

REQUIRED_FILES=(
    "results/correlations.csv"
    "results/model_summary.csv"
    "results/quality_report.csv"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "ERROR: Missing required artifact: $file"
        exit 1
    fi
    
    # Check if file is non-empty
    if [ ! -s "$file" ]; then
        echo "ERROR: Artifact is empty: $file"
        exit 1
    fi
    
    echo "  Found: $file ($(wc -l < "$file") lines)"
done

# 5. Verify correlations.csv schema
echo "Verifying correlations.csv schema..."
$PYTHON_CMD -c "
import pandas as pd
df = pd.read_csv('results/correlations.csv')
required_cols = ['metric', 'proxy', 'pearson_r', 'adj_p', 'method']
missing = [c for c in required_cols if c not in df.columns]
if missing:
    print(f'ERROR: Missing columns in correlations.csv: {missing}')
    exit(1)
print(f'Correlations schema OK. Columns: {list(df.columns)}')
"

if [ $? -ne 0 ]; then
    echo "ERROR: Schema validation failed"
    exit 1
fi

echo "=== Validation Complete ==="
echo "All checks passed at $(date)"
exit 0