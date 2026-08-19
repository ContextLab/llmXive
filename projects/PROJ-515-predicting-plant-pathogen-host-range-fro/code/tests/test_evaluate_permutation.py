import os
import json
import tempfile
import pandas as pd
import numpy as np
import pytest
from pathlib import Path

from src.models.evaluate import run_permutation_test, run_nested_cv, print_summary, calculate_auprc

@pytest.fixture
def sample_data():
    """Generate sample features and labels for testing."""
    np.random.seed(42)
    n_samples = 100
    n_features = 5
    
    X = pd.DataFrame(
        np.random.randn(n_samples, n_features),
        columns=[f"feature_{i}" for i in range(n_features)]
    )
    # Create a simple binary label with some signal
    y = pd.Series((X["feature_0"] + X["feature_1"] + np.random.randn(n_samples) * 0.5 > 0).astype(int))
    
    return X, y

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_run_permutation_test_basic(sample_data):
    """Test that permutation test runs and returns expected structure."""
    X, y = sample_data
    result = run_permutation_test(X, y, n_permutations=5, seed=42)
    
    assert isinstance(result, dict)
    assert "mean" in result
    assert "std" in result
    assert "scores" in result
    assert len(result["scores"]) == 5
    assert result["mean"] >= 0.0
    assert result["mean"] <= 1.0

def test_run_nested_cv_with_permutation(sample_data, temp_output_dir):
    """Test that nested CV runs and includes permutation logic."""
    X, y = sample_data
    # Use very small numbers for speed in unit test
    result = run_nested_cv(
        X, y, 
        n_outer_folds=2, 
        n_inner_folds=2, 
        seed=42, 
        n_permutations=2
    )
    
    assert isinstance(result, dict)
    assert "auprc_mean" in result
    assert "permutation_mean" in result
    assert "auprc_scores" in result
    assert "permutation_scores" in result
    
    # Check that we got results for both outer folds
    assert len(result["auprc_scores"]) == 2
    assert len(result["permutation_scores"]) == 2

def test_print_summary(sample_data):
    """Test that print_summary executes without error."""
    results = {
        "auprc_mean": 0.85,
        "auprc_std": 0.05,
        "precision_mean": 0.80,
        "permutation_mean": 0.45
    }
    # Just ensure it doesn't crash
    print_summary(results)