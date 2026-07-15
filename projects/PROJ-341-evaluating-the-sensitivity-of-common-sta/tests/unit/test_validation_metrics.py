import os
import json
import tempfile
import pytest
import numpy as np
import pandas as pd
from code.analysis.validation_metrics import (
    calculate_ks_distance,
    calculate_real_data_power,
    save_validation_metrics,
    VALIDATION_METRICS_PATH
)

def test_calculate_real_data_power():
    """Test the calculation of power (rejection rate) from real p-values."""
    p_values = [0.01, 0.02, 0.06, 0.5, 0.9]
    alpha = 0.05
    
    result = calculate_real_data_power(p_values, alpha)
    
    assert result["rejections"] == 2
    assert result["total_tests"] == 5
    assert abs(result["rejection_rate"] - 0.4) < 1e-6
    assert result["alpha"] == alpha

def test_calculate_real_data_power_empty():
    """Test handling of empty p-value list."""
    result = calculate_real_data_power([], 0.05)
    assert result["rejection_rate"] == 0.0
    assert result["count"] == 0

def test_calculate_ks_distance():
    """Test KS distance calculation between two distributions."""
    np.random.seed(42)
    dist1 = np.random.uniform(0, 1, 100)
    dist2 = np.random.uniform(0, 1, 100)
    
    ks_dist = calculate_ks_distance(dist1.tolist(), dist2.tolist())
    
    assert 0 <= ks_dist <= 1.0
    # For two uniform random distributions of size 100, KS should be small
    assert ks_dist < 0.25

def test_save_validation_metrics(tmp_path):
    """Test saving metrics to a JSON file."""
    test_metrics = {
        "ks_distance": 0.05,
        "validation_passed": True,
        "details": {"mean": 0.5}
    }
    output_file = str(tmp_path / "test_metrics.json")
    
    saved_path = save_validation_metrics(test_metrics, output_file)
    
    assert os.path.exists(saved_path)
    with open(saved_path, 'r') as f:
        loaded = json.load(f)
    
    assert loaded["ks_distance"] == 0.05
    assert loaded["validation_passed"] is True
