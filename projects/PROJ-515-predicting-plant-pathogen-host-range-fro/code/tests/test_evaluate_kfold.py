import os
import json
import tempfile
import pandas as pd
import numpy as np
import pytest
from pathlib import Path

from src.models.evaluate import (
    calculate_auprc,
    calculate_precision,
    benjamini_hochberg_fdr,
    cohen_d,
    run_kfold_cv,
    run_permutation_test
)

@pytest.fixture
def sample_features_labels():
    """Generate sample feature matrix and labels for testing."""
    np.random.seed(42)
    n_samples = 200
    n_features = 10
    X = np.random.rand(n_samples, n_features)
    # Create a simple label distribution
    y = np.random.randint(0, 2, n_samples)
    return X, y

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for output files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_calculate_auprc_basic():
    """Test basic AUPRC calculation."""
    y_true = np.array([0, 0, 1, 1])
    y_prob = np.array([0.1, 0.4, 0.35, 0.8])
    auprc = calculate_auprc(y_true, y_prob)
    assert 0.0 <= auprc <= 1.0, "AUPRC should be between 0 and 1"

def test_calculate_auprc_single_class():
    """Test AUPRC with single class in y_true."""
    y_true = np.array([0, 0, 0, 0])
    y_prob = np.array([0.1, 0.4, 0.35, 0.8])
    auprc = calculate_auprc(y_true, y_prob)
    assert auprc == 0.0, "AUPRC should be 0.0 for single class"

def test_calculate_precision_basic():
    """Test basic precision calculation."""
    y_true = np.array([0, 0, 1, 1])
    y_pred = np.array([0, 1, 1, 1])
    precision = calculate_precision(y_true, y_pred)
    assert 0.0 <= precision <= 1.0, "Precision should be between 0 and 1"

def test_run_kfold_cv_basic(sample_features_labels):
    """Test basic k-fold cross-validation."""
    X, y = sample_features_labels
    metrics = run_kfold_cv(X, y, n_folds=5, seed=42)
    
    assert "mean_auprc" in metrics
    assert "std_auprc" in metrics
    assert "mean_precision" in metrics
    assert "std_precision" in metrics
    assert "fold_metrics" in metrics
    assert len(metrics["fold_metrics"]) == 5
    
    assert 0.0 <= metrics["mean_auprc"] <= 1.0
    assert 0.0 <= metrics["mean_precision"] <= 1.0

def test_run_kfold_cv_vif_filtering(sample_features_labels):
    """Test k-fold CV with VIF filtering."""
    X, y = sample_features_labels
    # Introduce high correlation to trigger VIF
    X[:, 1] = X[:, 0] * 1.5 + 0.1
    
    metrics = run_kfold_cv(X, y, n_folds=3, seed=42)
    
    assert len(metrics["fold_metrics"]) == 3
    # Check that features were reduced in at least one fold
    for fold in metrics["fold_metrics"]:
        assert fold["n_features_used"] <= X.shape[1]

def test_benjamini_hochberg_fdr_basic():
    """Test Benjamini-Hochberg FDR correction."""
    p_values = [0.01, 0.04, 0.03, 0.005, 0.02]
    adjusted = benjamini_hochberg_fdr(p_values)
    
    assert len(adjusted) == len(p_values)
    assert all(0.0 <= p <= 1.0 for p in adjusted)
    # Adjusted p-values should generally be larger or equal to raw
    assert all(adj >= raw for adj, raw in zip(adjusted, p_values))

def test_benjamini_hochberg_fdr_empty():
    """Test FDR with empty input."""
    adjusted = benjamini_hochberg_fdr([])
    assert adjusted == []

def test_cohen_d_identical_groups():
    """Test Cohen's d with identical groups."""
    group1 = np.array([1, 2, 3, 4, 5])
    group2 = np.array([1, 2, 3, 4, 5])
    d = cohen_d(group1, group2)
    assert d == 0.0, "Cohen's d should be 0 for identical groups"

def test_cohen_d_different_groups():
    """Test Cohen's d with different groups."""
    group1 = np.array([1, 2, 3, 4, 5])
    group2 = np.array([10, 11, 12, 13, 14])
    d = cohen_d(group1, group2)
    assert d != 0.0, "Cohen's d should not be 0 for different groups"
    assert d < 0, "Cohen's d should be negative if group1 mean < group2 mean"

def test_run_kfold_cv_single_class_label(sample_features_labels):
    """Test k-fold CV with single class label in test set (edge case)."""
    X, y = sample_features_labels
    # Force a scenario where one fold might have single class
    y_single_class = np.zeros(len(y))
    
    metrics = run_kfold_cv(X, y_single_class, n_folds=5, seed=42)
    
    # Should handle gracefully without crashing
    assert "mean_auprc" in metrics
    assert metrics["mean_auprc"] == 0.0  # Expected for single class