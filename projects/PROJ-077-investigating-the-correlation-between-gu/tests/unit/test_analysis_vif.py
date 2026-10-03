"""Tests for VIF calculation in analysis module."""
import pytest
import pandas as pd
import numpy as np
import json
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from code.analysis import calculate_vif, save_vif_results

@pytest.fixture
def sample_data():
    """Create a sample DataFrame with some multicollinearity."""
    np.random.seed(42)
    n = 100
    df = pd.DataFrame({
        "feature_a": np.random.randn(n),
        "feature_b": np.random.randn(n),
        "feature_c": np.random.randn(n),
        "target": np.random.randn(n)
    })
    # Add perfect multicollinearity for testing
    df["feature_d"] = df["feature_a"] * 2 + 1
    return df

def test_calculate_vif_returns_dict(sample_data):
    """Test that VIF calculation returns a dictionary."""
    result = calculate_vif(sample_data, exclude_cols=["target"])
    assert isinstance(result, dict)
    assert "feature_a" in result
    assert result["feature_a"] > 0

def test_calculate_vif_handles_multicollinearity(sample_data):
    """Test that VIF correctly identifies multicollinearity (feature_d should have high VIF)."""
    result = calculate_vif(sample_data, exclude_cols=["target"])
    # feature_d is perfectly correlated with feature_a, so VIF should be very high (or inf)
    # Due to floating point, it might not be exactly inf, but should be > 10
    assert result["feature_d"] > 10 or np.isinf(result["feature_d"])

def test_save_vif_results_creates_file(sample_data, tmp_path):
    """Test that save_vif_results creates a JSON file."""
    vif_results = calculate_vif(sample_data, exclude_cols=["target"])
    output_path = str(tmp_path / "vif_results.json")
    save_vif_results(vif_results, output_path)
    
    assert Path(output_path).exists()
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    assert "feature_a" in data
    assert data["feature_a"] > 0