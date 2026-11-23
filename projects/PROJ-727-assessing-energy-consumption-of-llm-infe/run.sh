#!/bin/bash
# run.sh - Entry point for the energy consumption pipeline.
# This script verifies the environment, runs the full pipeline, and logs the duration.

set -e

echo "=========================================="
echo "Starting Energy Consumption Pipeline"
echo "=========================================="

# 1. Environment Verification (T008a)
echo "Verifying environment..."
python -c "
import sys
try:
    import torch
    import transformers
    import codecarbon
    import pandas as pd
    import numpy as np
    print('Environment Verified: All core dependencies found.')
except ImportError as e:
    print(f'Environment Verification Failed: {e}', file=sys.stderr)
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo "Environment verification failed. Exiting."
    exit 1
fi

# 2. Run Full Pipeline with Timing (T034)
echo "Running full pipeline with timing..."
python code/pipeline_timer.py

if [ $? -ne 0 ]; then
    echo "Pipeline execution failed. Check logs."
    exit 1
fi

# 3. Final Validation (T035)
echo "Running final validation..."
python code/final_validation.py

if [ $? -ne 0 ]; then
    echo "Final validation failed. Check logs."
    exit 1
fi

echo "=========================================="
echo "Pipeline Completed Successfully"
echo "=========================================="
