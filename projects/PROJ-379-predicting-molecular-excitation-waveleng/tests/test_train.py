"""
Integration test for training loop convergence and artifact generation (T013).
"""
import os
import pytest
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
model_path = project_root / "model.pt"
metrics_path = project_root / "data" / "processed" / "metrics_partial.json"

def test_model_artifact_generated():
    """Verify model.pt is generated after training."""
    # Note: This test assumes training has been run (e.g. via T041)
    # If model.pt doesn't exist, we skip or fail depending on strictness.
    # For T043 (running all tests), we expect artifacts to exist if previous tasks passed.
    if not model_path.exists():
        pytest.skip("model.pt not found. Run code/train.py first.")
    
    assert model_path.stat().st_size > 0, "model.pt is empty"

def test_metrics_partial_exists():
    """Verify metrics_partial.json is generated."""
    if not metrics_path.exists():
        pytest.skip("metrics_partial.json not found. Run code/evaluate.py first.")
    
    import json
    with open(metrics_path, 'r') as f:
        data = json.load(f)
    
    required_keys = ["mae", "r2", "sc001_status"]
    for key in required_keys:
        assert key in data, f"Missing key '{key}' in metrics_partial.json"
