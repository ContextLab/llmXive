import os
import json
import tempfile
import pandas as pd
import numpy as np
import pytest
from pathlib import Path
from sklearn.metrics import average_precision_score

from src.models.evaluate import run_nested_cv, run_permutation_test, print_summary
from src.models.train import train_model_fold

@pytest.fixture
def sample_data():
    """Generate a small synthetic dataset for testing permutation logic."""
    np.random.seed(42)
    n_samples = 100
    n_features = 10
    
    # Create features
    X = pd.DataFrame(np.random.randn(n_samples, n_features), 
                     columns=[f"feat_{i}" for i in range(n_features)])
    
    # Create labels with some signal
    # y = 1 if sum of first 3 features > 0
    signal = X.iloc[:, :3].sum(axis=1)
    y = (signal > 0).astype(int)
    
    return X, y

@pytest.fixture
def temp_output_dir(tmp_path):
    return tmp_path

def test_run_permutation_test_basic(sample_data, temp_output_dir):
    """Test that permutation test returns a baseline and a list of permuted scores."""
    X, y = sample_data
    n = len(X)
    train_size = int(0.8 * n)
    
    X_train, X_val = X.iloc[:train_size], X.iloc[train_size:]
    y_train, y_val = y.iloc[:train_size], y.iloc[train_size:]
    
    baseline, perm_list = run_permutation_test(
        X_train=X_train,
        y_train=y_train,
        X_val=X_val,
        y_val=y_val,
        n_permutations=3,
        random_state=42,
        fold_idx=0
    )
    
    assert isinstance(baseline, float), "Baseline should be a float"
    assert isinstance(perm_list, list), "Permuted list should be a list"
    assert len(perm_list) == 3, "Should have 3 permuted scores"
    
    # Baseline should generally be higher than permuted scores if signal exists
    # (Though with small data, this isn't guaranteed, but we check types and existence)
    assert all(isinstance(p, float) for p in perm_list)

def test_run_nested_cv_with_permutation(sample_data, temp_output_dir):
    """Test that nested CV runs and includes permutation results."""
    X, y = sample_data
    
    # Reduce folds for speed
    results = run_nested_cv(
        X=X,
        y=y,
        n_outer_folds=2,
        n_inner_folds=2,
        n_permutations=2,
        seed=42,
        output_dir=temp_output_dir
    )
    
    assert "mean_outer_auprc" in results
    assert "permutation_summary" in results
    assert isinstance(results["mean_outer_auprc"], float)
    assert len(results["permutation_summary"]) == 2 # 2 outer folds
    
    # Check permutation summary structure
    for item in results["permutation_summary"]:
        assert "fold" in item
        assert "p_value" in item
        assert "significant" in item
        assert 0.0 <= item["p_value"] <= 1.0

def test_print_summary(sample_data, temp_output_dir, caplog):
    """Test that print_summary runs without error."""
    X, y = sample_data
    results = run_nested_cv(
        X=X,
        y=y,
        n_outer_folds=2,
        n_inner_folds=2,
        n_permutations=2,
        seed=42,
        output_dir=temp_output_dir
    )
    
    # This should not raise
    print_summary(results)
    # Verify output contains expected keys (loguru captures to stderr usually, but we check logic)
    # The function logs, so we just ensure it runs.
    assert results["mean_outer_auprc"] >= 0.0