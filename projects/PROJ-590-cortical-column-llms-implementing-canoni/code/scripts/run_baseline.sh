#!/bin/bash
# scripts/run_baseline.sh
# T013b: Explicitly call data generation functions for training and testing
# before running the baseline training loop.
#
# This script ensures independent synthetic datasets are generated (Lorenz for
# training, Polynomials/Fourier for testing) and then invokes the baseline
# trainer. It satisfies FR-006 by enforcing data independence via the
# generate_training_data / generate_test_data pipeline.

set -e

# Project root relative to script location
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

# Ensure output directories exist
mkdir -p data/results data/logs

echo "=== Step 1: Generate Independent Training Data ==="
# Calls src.data.benchmarks.generate_training_data (Lorenz Attractor)
# Outputs: data/results/train_data.npy, data/results/train_meta.json
python - << 'PYEOF'
import sys
import os
# Ensure project root is in path
sys.path.insert(0, os.path.abspath('.'))

from src.data.benchmarks import generate_training_data, generate_test_data, verify_independence
import numpy as np
import json
from pathlib import Path

DATA_DIR = Path("data/results")
DATA_DIR.mkdir(parents=True, exist_ok=True)

print("Generating training data (Lorenz Attractor)...")
train_X, train_y, train_meta = generate_training_data(
    n_samples=10000, 
    sequence_length=50, 
    seed=42,
    noise_level=0.01
)

# Save training data
np.save(DATA_DIR / "train_data.npy", train_X)
np.save(DATA_DIR / "train_targets.npy", train_y)
with open(DATA_DIR / "train_meta.json", "w") as f:
    json.dump(train_meta, f, indent=2)

print(f"Training data saved: {train_X.shape}, {train_y.shape}")

print("Generating test data (Polynomials/Fourier)...")
test_X, test_y, test_meta = generate_test_data(
    n_samples=2000, 
    sequence_length=50, 
    seed=123,
    noise_level=0.01
)

# Save test data
np.save(DATA_DIR / "test_data.npy", test_X)
np.save(DATA_DIR / "test_targets.npy", test_y)
with open(DATA_DIR / "test_meta.json", "w") as f:
    json.dump(test_meta, f, indent=2)

print(f"Test data saved: {test_X.shape}, {test_y.shape}")

# Verify independence (KS Test)
print("Verifying statistical independence between train and test distributions...")
is_independent = verify_independence(train_X, test_X)
print(f"Independence check (KS Test): {'PASSED' if is_independent else 'WARNING: Distributions may be similar'}")

# Save verification result
with open(DATA_DIR / "data_independence_report.json", "w") as f:
    json.dump({"independent": is_independent, "train_shape": list(train_X.shape), "test_shape": list(test_X.shape)}, f)

print("Data generation complete.")
PYEOF

echo ""
echo "=== Step 2: Run Baseline Training ==="
# Invokes the baseline runner which loads the data generated above
python code/scripts/run_baseline_training.py \
    --train-data data/results/train_data.npy \
    --train-targets data/results/train_targets.npy \
    --test-data data/results/test_data.npy \
    --test-targets data/results/test_targets.npy \
    --output-dir data/results \
    --log-file data/logs/baseline_run.log

echo ""
echo "=== Baseline Pipeline Complete ==="
echo "Results available in: data/results/"