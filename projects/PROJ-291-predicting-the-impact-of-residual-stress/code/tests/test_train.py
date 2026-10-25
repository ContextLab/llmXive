"""
test_train.py
---------------
Unit tests for the training script (task T005).

The tests verify that:
  1. The training script runs without error.
  2. Model artefacts are created under the expected directory structure.
  3. The shallow neural network respects the 3600‑second training‑time limit.
"""

import json
from pathlib import Path

import pytest

from src.train import main as train_main

# Paths (relative to the project root)
MODEL_ROOT = Path("code/models")
PERF_CSV = Path("data/results/model_performance.csv")

@pytest.fixture(scope="module")
def run_training():
    """Execute the training pipeline once for the whole test module."""
    train_main()
    assert PERF_CSV.is_file(), "Performance CSV was not created"
    return {
        "model_root": MODEL_ROOT,
        "perf_csv": PERF_CSV,
    }

def _find_model_files(root: Path):
    """Collect all model files under the given root."""
    return list(root.rglob("model.*"))

def test_model_files_exist(run_training):
    """All expected model artefacts must exist."""
    root = run_training["model_root"]
    model_files = _find_model_files(root)
    # Expect four feature sets × three algorithms = 12 model files
    assert len(model_files) == 12, f"Expected 12 model files, found {len(model_files)}"

def test_nn_training_time_limit(run_training):
    """NN training time must be ≤ 3600 s (checked via the logged CSV)."""
    perf_path = run_training["perf_csv"]
    df = pd.read_csv(perf_path)
    nn_times = df[df["algorithm"] == "NN"]["train_time_s"].dropna()
    assert not nn_times.empty, "No NN training times recorded"
    assert nn_times.max() <= 3600, f"NN training exceeded limit: {nn_times.max()} s"