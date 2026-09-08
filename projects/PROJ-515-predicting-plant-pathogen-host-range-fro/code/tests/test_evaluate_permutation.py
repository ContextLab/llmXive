import os
import json
import tempfile
import pandas as pd
import numpy as np
import pytest
from pathlib import Path

from src.models.evaluate import run_permutation_test, run_nested_cv, print_summary

@pytest.fixture
def sample_data():
    # Create a small synthetic dataset for testing
    np.random.seed(42)
    n_samples = 100
    n_features = 10
    X = np.random.rand(n_samples, n_features)
    y = np.random.randint(0, 2, n_samples)
    return X, y

@pytest.fixture
def temp_output_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_run_permutation_test_basic(sample_data, temp_output_dir):
    X, y = sample_data
    # Run a quick permutation test with few permutations
    results = run_permutation_test(
        X, y, 
        n_permutations=5, 
        n_splits=3, 
        output_dir=temp_output_dir
    )
    
    assert "mean_perm_auprc" in results
    assert "std_perm_auprc" in results
    assert "scores" in results
    assert len(results["scores"]) == 5
    assert isinstance(results["mean_perm_auprc"], float)

def test_run_nested_cv_with_permutation(sample_data, temp_output_dir):
    X, y = sample_data
    # Run nested CV with permutation test enabled
    results = run_nested_cv(
        X, y,
        n_outer=3,
        n_inner=2,
        n_permutations=3,
        output_dir=temp_output_dir
    )
    
    assert "mean_outer_auprc" in results
    assert "permutation_test_results" in results
    assert len(results["permutation_test_results"]) == 3
    
    for res in results["permutation_test_results"]:
        assert "real_inner_mean" in res
        assert "perm_mean" in res
        assert "perm_scores" in res

def test_print_summary(sample_data, temp_output_dir):
    X, y = sample_data
    results = run_nested_cv(
        X, y,
        n_outer=2,
        n_inner=2,
        output_dir=temp_output_dir
    )
    # Should not raise
    print_summary(results)