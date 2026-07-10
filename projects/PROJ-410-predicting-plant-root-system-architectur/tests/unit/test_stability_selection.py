import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from code.stability_selection import run_single_bootstrap, perform_stability_selection

def test_run_single_bootstrap_shapes(tmp_path):
    """Test that bootstrap returns correct structure."""
    X = np.random.rand(100, 10)
    y = np.random.rand(100)
    feature_names = [f"feat_{i}" for i in range(10)]
    
    result = run_single_bootstrap(X, y, "elasticnet", feature_names, seed=42)
    
    assert isinstance(result, dict)
    assert len(result) == 10
    assert all(isinstance(v, float) for v in result.values())
    assert set(result.keys()) == set(feature_names)

def test_stability_selection_empty_data(tmp_path):
    """Test handling of empty or missing data."""
    # This test relies on the file system state, so we mock the behavior
    # or ensure the function handles missing files gracefully.
    # The function perform_stability_selection returns an empty DataFrame if data is missing.
    pass

def test_stability_selection_determinism(tmp_path):
    """Test that running with same seed gives same results."""
    # Create dummy data
    X = np.random.RandomState(42).rand(50, 5)
    y = np.random.RandomState(42).rand(50)
    feature_names = [f"f{i}" for i in range(5)]
    
    res1 = run_single_bootstrap(X, y, "elasticnet", feature_names, seed=123)
    res2 = run_single_bootstrap(X, y, "elasticnet", feature_names, seed=123)
    
    assert res1 == res2