#!/bin/bash
# Quickstart validation script for PROJ-174
# Executes the pipeline and verifies the primary output artifact exists.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CODE_DIR="$PROJECT_ROOT/code"

echo "=== llmXive Quickstart Validation ==="
echo "Project Root: $PROJECT_ROOT"
echo "Code Dir: $CODE_DIR"

# Change to code directory to run the pipeline
cd "$CODE_DIR"

# Verify environment setup (virtual env, dependencies)
if [ ! -d "venv" ]; then
    echo "[WARN] Virtual environment not found. Attempting to create..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Run the main pipeline
# This orchestrates: Data Verification -> Preprocessing -> Analysis (US1)
echo "Running main pipeline..."
python main.py

# Verification: Check for the specific output artifact required by T037
RESULT_FILE="$PROJECT_ROOT/results/correlations.csv"

if [ -f "$RESULT_FILE" ]; then
    echo "[SUCCESS] Output artifact found: $RESULT_FILE"
    echo "File size: $(wc -c < "$RESULT_FILE") bytes"
    echo "First 5 lines:"
    head -n 5 "$RESULT_FILE"
    exit 0
else
    echo "[FAILURE] Expected output file not found: $RESULT_FILE"
    echo "The pipeline may have failed or produced output in a different location."
    exit 1
fi