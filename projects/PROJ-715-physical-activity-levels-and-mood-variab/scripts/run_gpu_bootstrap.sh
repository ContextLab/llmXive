#!/usr/bin/env bash
set -euo pipefail

# GPU Offload Script for T061
# This script is designed to be picked up by the execution stage's auto-offload mechanism
# when T060 detects a CPU timeout or memory error during the bootstrap sensitivity analysis.

# Set CUDA device visibility to the first available GPU
export CUDA_VISIBLE_DEVICES=0

echo "Starting GPU-accelerated bootstrap sensitivity analysis..."
echo "Device: CUDA_VISIBLE_DEVICES=$CUDA_VISIBLE_DEVICES"

# Execute the specific analysis task with CUDA device
python code/analysis.py --task run_sensitivity_single_rating_bootstrap --device cuda

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "GPU bootstrap analysis completed successfully."
else
    echo "GPU bootstrap analysis failed with exit code $EXIT_CODE."
    exit $EXIT_CODE
fi