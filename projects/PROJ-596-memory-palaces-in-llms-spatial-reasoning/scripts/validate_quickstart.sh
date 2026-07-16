#!/bin/bash
# T033: Quickstart Validation Script
# Runs a minimal end-to-end pipeline and verifies artifacts are produced within time limits.

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "=== llmXive Quickstart Validation ==="
echo "Project Root: $PROJECT_ROOT"
echo "Start Time: $(date -u +%Y-%m-%dT%H:%M:%SZ)"

START_TIME=$(date +%s)
TIME_LIMIT=18000  # 5 hours in seconds

# Ensure artifacts directory exists
mkdir -p artifacts/results

echo "Step 1: Verifying dataset downloads..."
# Run download script to ensure datasets are present
python code/data/download.py --verify-only

echo "Step 2: Running minimal training and evaluation loop..."
# Run the main entry point with a minimal configuration
# We assume the main.py handles the seed loop and dataset selection
python code/main.py --minimal-run

END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))

echo "Step 3: Verifying output artifacts..."

# Check for run_summary.json
if [ ! -f "artifacts/results/run_summary.json" ]; then
    echo "ERROR: artifacts/results/run_summary.json not found."
    exit 1
fi

# Check for hyperparams_log.json
if [ ! -f "artifacts/results/hyperparams_log.json" ]; then
    echo "ERROR: artifacts/results/hyperparams_log.json not found."
    exit 1
fi

# Check for statistical_summary.json (if applicable in minimal run)
if [ ! -f "artifacts/results/statistical_summary.json" ]; then
    echo "WARNING: statistical_summary.json not found (may be skipped in minimal run)."
fi

echo "Step 4: Validating runtime constraints..."
if [ $ELAPSED -gt $TIME_LIMIT ]; then
    echo "ERROR: Execution exceeded 5-hour limit ($ELAPSED seconds)."
    exit 1
fi

echo "Validation Successful!"
echo "Total Runtime: $ELAPSED seconds"
echo "End Time: $(date -u +%Y-%m-%dT%H:%M:%SZ)"

# Output summary to stdout
cat artifacts/results/run_summary.json
exit 0
