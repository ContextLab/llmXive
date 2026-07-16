#!/bin/bash
# Run full pipeline integration test (T033)

set -e

echo "=========================================="
echo "Running SN1 Pipeline Integration Test"
echo "=========================================="

# Change to code directory
cd "$(dirname "$0")"

# Create necessary directories
mkdir -p ../data/processed
mkdir -p ../artifacts
mkdir -p ../artifacts/integration_test

# Run the integration test
echo "Starting integration test..."
python -m pytest tests/integration/test_full_pipeline.py -v -s --tb=short

# Check exit code
if [ $? -eq 0 ]; then
    echo "=========================================="
    echo "Integration Test PASSED"
    echo "=========================================="
    echo "Check artifacts/integration_test/ for summary reports"
else
    echo "=========================================="
    echo "Integration Test FAILED"
    echo "=========================================="
    exit 1
fi