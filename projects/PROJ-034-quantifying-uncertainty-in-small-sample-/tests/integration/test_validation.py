"""
Integration tests for validation module (UCI dataset loading and subsampling).

These tests verify the real-world data pipeline for User Story 3 (US3).
They ensure that the UCI Concrete dataset can be fetched and subsampled
correctly for small-sample analysis.
"""
import pytest
import numpy as np
import os
from pathlib import Path
from validation.uci_runner import fetch_uci_concrete_dataset, subsample_stratified

def test_uci_dataset_loading():
    """
    Integration test for UCI dataset loading.
    
    Verifies that the real UCI Concrete Compressive Strength dataset
    can be fetched and loaded into memory with expected structure.
    """
    # This test checks if the data can be fetched from the real source.
    # It will fail loudly if the network is unavailable or the source URL changes,
    # satisfying the "fail loudly" constraint.
    data = fetch_uci_concrete_dataset()
    
    assert data is not None, "Dataset fetch returned None"
    assert "data" in data, "Missing 'data' key in dataset"
    assert "target" in data, "Missing 'target' key in dataset"
    
    # Check basic properties
    X = data["data"]
    y = data["target"]
    
    assert X.shape[0] > 0, "Dataset has no samples"
    assert y.shape[0] > 0, "Target has no samples"
    assert X.shape[0] == y.shape[0], "Shape mismatch between X and y"
    
    # Verify predictor count (Concrete dataset typically has 8 features)
    assert X.shape[1] >= 3, f"Expected at least 3 predictors, got {X.shape[1]}"
    
def test_uci_subsampling():
    """
    Integration test for UCI dataset subsampling.
    
    Verifies that stratified subsampling works correctly and preserves
    the necessary conditions for regression (N > p, variance in target).
    """
    # Fetch full dataset
    full_data = fetch_uci_concrete_dataset()
    X = full_data["data"]
    y = full_data["target"]
    
    # Subsample to N=40 (small sample regime)
    n_sample = 40
    p_features = X.shape[1]
    
    # Ensure we don't request a sample size <= features (rank deficiency)
    assert n_sample > p_features, f"Sample size {n_sample} must be > features {p_features}"
    
    X_sub, y_sub, indices = subsample_stratified(X, y, n=n_sample)
    
    assert X_sub.shape[0] == n_sample, f"Expected {n_sample} samples, got {X_sub.shape[0]}"
    assert y_sub.shape[0] == n_sample, f"Expected {n_sample} targets, got {y_sub.shape[0]}"
    assert X_sub.shape[1] == X.shape[1], "Feature dimension changed during subsampling"
    
    # Verify stratification: target should retain variance
    assert np.std(y_sub) > 0, "Subsampled target has zero variance; stratification failed"
    
    # Verify indices are valid
    assert len(indices) == n_sample, "Indices length mismatch"
    assert all(0 <= idx < len(y) for idx in indices), "Invalid indices generated"

def test_subsampling_rank_defense():
    """
    Test that subsampling handles cases where N <= p gracefully or raises correctly.
    """
    full_data = fetch_uci_concrete_dataset()
    X = full_data["data"]
    y = full_data["target"]
    
    p_features = X.shape[1]
    n_invalid = p_features  # Request exactly p samples (rank deficient for regression)
    
    # This should raise an error or handle the logic as defined in subsample_stratified
    # The implementation in uci_runner.py should validate N > p.
    with pytest.raises(ValueError) as excinfo:
        subsample_stratified(X, y, n=n_invalid)
    
    assert "Rank-deficient" in str(excinfo.value) or "N must be greater" in str(excinfo.value)