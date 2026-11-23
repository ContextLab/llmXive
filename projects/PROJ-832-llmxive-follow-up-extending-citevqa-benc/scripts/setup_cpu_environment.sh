#!/bin/bash
# Setup script for CPU-only execution environment
# This script configures the environment variables and validates CPU-only constraints

set -e

echo "Setting up CPU-only execution environment..."

# Set environment variables for CPU-only execution
export CUDA_VISIBLE_DEVICES=-1
export CUDA_DEVICE_ORDER=PCI_BUS_ID
export TORCH_USE_CUDA_DSA=0
export HF_HUB_OFFLINE=0
export TRANSFORMERS_OFFLINE=0

echo "Environment variables set:"
echo "  CUDA_VISIBLE_DEVICES=$CUDA_VISIBLE_DEVICES"
echo "  CUDA_DEVICE_ORDER=$CUDA_DEVICE_ORDER"
echo "  TORCH_USE_CUDA_DSA=$TORCH_USE_CUDA_DSA"
echo "  HF_HUB_OFFLINE=$HF_HUB_OFFLINE"
echo "  TRANSFORMERS_OFFLINE=$TRANSFORMERS_OFFLINE"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
else
    echo "No virtual environment found. Please run 'python -m venv venv' and install requirements first."
    exit 1
fi

# Run the CPU environment setup script
echo "Running CPU environment configuration..."
python code/setup_cpu_env.py

# Verify the setup
if [ $? -eq 0 ]; then
    echo "CPU-only environment setup completed successfully!"
else
    echo "CPU-only environment setup failed!"
    exit 1
fi
