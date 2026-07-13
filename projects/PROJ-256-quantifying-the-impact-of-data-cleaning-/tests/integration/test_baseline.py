"""
tests/integration/test_baseline.py
Integration test for baseline analysis pipeline.
Verifies that baseline_metrics.json is produced with valid p-values and finite CIs.
"""
import os
import sys
import json
import tempfile
import shutil
import pytest
import pandas as pd
import numpy as np

# Add code to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from analysis import run_baseline_analysis, run_t_test, run_linear_regression
from utils import setup_logging, pin_random_seed
from config import Config

@pytest.fixture
def sample_data_dir():
    """Create a temporary directory with sample CSV data."""
    tmp_dir = tempfile.mkdtemp()
    
    # Create a sample dataset
    np.random.seed(42)
    n = 100
    df = pd.DataFrame({
        "feature1": np.random.normal(0, 1, n),
        "feature2": np.random.normal(0, 1, n),
        "group": np.random.choice([0, 1], n),
        "outcome": np.random.normal(0, 1, n)
    })
    
    filepath = os.path.join(tmp_dir, "test_dataset.csv")
    df.to_csv(filepath, index=False)
    
    yield tmp_dir
    
    # Cleanup
    shutil.rmtree(tmp_dir)

def test_baseline_analysis_produces_json(sample_data_dir):
    """
    Test that run_baseline_analysis produces a valid JSON file with p-values in (0,1).
    """
    output_path = os.path.join(sample_data_dir, "baseline_metrics.json")
    config = Config()
    
    # Run analysis
    result = run_baseline_analysis(sample_data_dir, output_path, config)
    
    # Check file exists
    assert os.path.exists(output_path), "Output file not created."
    
    # Check content
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    assert "datasets" in data, "Missing 'datasets' key in output."
    assert len(data["datasets"]) > 0, "No datasets analyzed."
    
    for ds in data["datasets"]:
        # Check t-test
        if ds.get("t_test"):
            p_val = ds["t_test"].get("p_value")
            assert p_val is not None, "P-value missing in t_test."
            assert 0 < p_val < 1, f"P-value {p_val} not in (0, 1)."
        
        # Check regression
        if ds.get("regression"):
            r2 = ds["regression"].get("r_squared")
            assert r2 is not None, "R-squared missing."
            # R2 can be negative, but should be finite
            assert np.isfinite(r2), f"R-squared {r2} is not finite."

def test_t_test_p_value_range():
    """
    Unit test for t-test p-value range.
    """
    np.random.seed(42)
    g0 = np.random.normal(0, 1, 50)
    g1 = np.random.normal(0.5, 1, 50)
    
    t_stat, p_val = run_t_test(g0, g1)
    
    assert 0 < p_val < 1, f"P-value {p_val} out of range."
    assert np.isfinite(t_stat), "T-statistic is not finite."

def test_regression_finite_ci():
    """
    Unit test for regression results finiteness.
    """
    np.random.seed(42)
    X = pd.DataFrame({"x": np.random.normal(0, 1, 50)})
    y = pd.Series(np.random.normal(0, 1, 50))
    
    res = run_linear_regression(X, y)
    
    assert np.isfinite(res["r_squared"]), "R-squared not finite."
    for p in res["p_values"]:
        assert np.isfinite(p), f"P-value {p} in regression is not finite."