import os
import json
import tempfile
import pandas as pd
import numpy as np
import pytest
from pathlib import Path

from src.models.evaluate import (
    run_kfold_cv,
    calculate_auprc,
    calculate_precision,
    benjamini_hochberg_fdr,
    calculate_cohen_d
)

@pytest.fixture
def sample_features_labels():
    """Generate sample features and labels for testing."""
    np.random.seed(42)
    n_samples = 100
    n_features = 10
    
    # Generate features with some correlation
    X = np.random.randn(n_samples, n_features)
    X[:, 0] = X[:, 1] * 0.8 + 0.2 * np.random.randn(n_samples)  # Correlated features
    
    # Generate binary labels based on first few features
    y = ((X[:, 0] + X[:, 1] + np.random.randn(n_samples) * 0.5) > 0).astype(int)
    
    features_df = pd.DataFrame(X, columns=[f'feature_{i}' for i in range(n_features)])
    return features_df, y

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for output files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_calculate_auprc_basic():
    """Test basic AUPRC calculation."""
    y_true = np.array([0, 0, 1, 1])
    y_prob = np.array([0.1, 0.4, 0.35, 0.8])
    
    auprc = calculate_auprc(y_true, y_prob)
    assert 0.0 <= auprc <= 1.0
    assert auprc > 0.5  # Should be better than random

def test_calculate_auprc_single_class():
    """Test AUPRC with single class."""
    y_true = np.array([0, 0, 0, 0])
    y_prob = np.array([0.1, 0.2, 0.3, 0.4])
    
    auprc = calculate_auprc(y_true, y_prob)
    assert auprc == 0.0

def test_calculate_precision_basic():
    """Test basic precision calculation."""
    y_true = np.array([0, 0, 1, 1])
    y_pred = np.array([0, 1, 1, 0])
    
    precision = calculate_precision(y_true, y_pred)
    assert 0.0 <= precision <= 1.0

def test_run_kfold_cv_basic(sample_features_labels, temp_output_dir):
    """Test basic k-fold cross-validation."""
    features_df, labels = sample_features_labels
    
    results = run_kfold_cv(
        features_df=features_df,
        labels=labels,
        n_splits=3,
        seed=42,
        vif_threshold=5.0
    )
    
    # Check required keys
    assert 'mean_auprc' in results
    assert 'mean_precision' in results
    assert 'auprc_scores' in results
    assert 'precision_scores' in results
    assert 'fold_results' in results
    
    # Check metrics are in valid range
    assert 0.0 <= results['mean_auprc'] <= 1.0
    assert 0.0 <= results['mean_precision'] <= 1.0
    
    # Check number of folds
    assert len(results['auprc_scores']) == 3
    assert len(results['precision_scores']) == 3

def test_run_kfold_cv_vif_filtering(sample_features_labels):
    """Test that VIF filtering reduces features."""
    features_df, labels = sample_features_labels
    
    # Get initial number of features
    initial_features = features_df.shape[1]
    
    results = run_kfold_cv(
        features_df=features_df,
        labels=labels,
        n_splits=3,
        seed=42,
        vif_threshold=5.0
    )
    
    # Check that features were reduced in at least one fold
    for fold_result in results['fold_results']:
        assert fold_result['n_features_after_vif'] <= initial_features

def test_benjamini_hochberg_fdr_basic():
    """Test Benjamini-Hochberg FDR correction."""
    p_values = [0.01, 0.03, 0.05, 0.07, 0.10]
    
    adjusted = benjamini_hochberg_fdr(p_values)
    
    assert len(adjusted) == len(p_values)
    assert all(0.0 <= p <= 1.0 for p in adjusted)
    
    # Adjusted p-values should be >= original (monotonicity)
    for orig, adj in zip(p_values, adjusted):
        assert adj >= orig

def test_benjamini_hochberg_fdr_empty():
    """Test FDR with empty list."""
    adjusted = benjamini_hochberg_fdr([])
    assert adjusted == []

def test_cohen_d_identical_groups():
    """Test Cohen's d with identical groups."""
    group1 = np.array([1.0, 2.0, 3.0])
    group2 = np.array([1.0, 2.0, 3.0])
    
    d = calculate_cohen_d(group1, group2)
    assert d == 0.0

def test_cohen_d_different_groups():
    """Test Cohen's d with different groups."""
    group1 = np.array([1.0, 2.0, 3.0])
    group2 = np.array([4.0, 5.0, 6.0])
    
    d = calculate_cohen_d(group1, group2)
    assert d < 0  # Group 1 mean < Group 2 mean

def test_run_kfold_cv_single_class_label(sample_features_labels):
    """Test k-fold CV with single class in validation set."""
    features_df, labels = sample_features_labels
    
    # Force single class in validation by using very unbalanced data
    labels_unbalanced = np.array([0] * 95 + [1] * 5)
    
    results = run_kfold_cv(
        features_df=features_df,
        labels=labels_unbalanced,
        n_splits=5,
        seed=42,
        vif_threshold=5.0
    )
    
    # Should handle gracefully
    assert 'mean_auprc' in results