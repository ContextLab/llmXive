import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import json
import tempfile
import os

# Mock the environment config to use a temporary directory for testing
# We will patch the get_processed_dir function if necessary, or set env vars.
# For this test, we assume the environment is set up correctly or we mock the data loading.

from report_regression_metrics import calculate_regression_metrics, save_metrics_report

@pytest.fixture
def sample_data():
    """Create a small synthetic dataset for testing the metric calculation logic."""
    n_samples = 50
    n_features = 5
    
    # Generate random features
    X = pd.DataFrame(
        np.random.rand(n_samples, n_features),
        columns=[f"feature_{i}" for i in range(n_features)]
    )
    
    # Generate a target with a known relationship + noise
    # y = 2*feature_0 + 1*feature_1 + noise
    y = 2 * X["feature_0"] + 1 * X["feature_1"] + np.random.normal(0, 0.1, n_samples)
    
    return X, y, list(X.columns)

def test_regression_metrics_calculation(sample_data):
    """Test that the metric calculation function returns expected structure and valid values."""
    X, y, feature_names = sample_data
    
    metrics = calculate_regression_metrics(X, y, feature_names, top_n=3)
    
    # Check structure
    assert "mean_r2" in metrics
    assert "std_r2" in metrics
    assert "n_samples" in metrics
    assert "cv_strategy" in metrics
    assert "top_features" in metrics
    
    # Check types and ranges
    assert isinstance(metrics["mean_r2"], float)
    assert -1.0 <= metrics["mean_r2"] <= 1.0  # R2 can be negative but usually < 1 for noisy data
    assert metrics["std_r2"] >= 0.0
    assert metrics["n_samples"] == 50
    
    # Check top features
    assert len(metrics["top_features"]) == 3
    for feat in metrics["top_features"]:
        assert "feature" in feat
        assert "importance" in feat
        assert "p_value" in feat
        assert isinstance(feat["p_value"], float)
    
    # Since we constructed y with feature_0 and feature_1, they should likely be top
    top_names = [f["feature"] for f in metrics["top_features"]]
    assert "feature_0" in top_names or "feature_1" in top_names

def test_save_metrics_report(sample_data):
    """Test that the report is saved correctly to a JSON file."""
    X, y, feature_names = sample_data
    metrics = calculate_regression_metrics(X, y, feature_names, top_n=3)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_metrics.json"
        save_metrics_report(metrics, output_path)
        
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            loaded_metrics = json.load(f)
        
        assert loaded_metrics["mean_r2"] == metrics["mean_r2"]
        assert loaded_metrics["std_r2"] == metrics["std_r2"]
        assert len(loaded_metrics["top_features"]) == 3