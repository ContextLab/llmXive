"""
Unit tests for diagnostics module (User Story 3).
"""
import numpy as np
import pandas as pd
import pytest
from scipy import stats
from sklearn.linear_model import ElasticNet

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from code.diagnostics import (
    calculate_permutation_importance,
    calculate_vif,
    run_median_split_sensitivity,
    run_regularization_sensitivity
)

@pytest.fixture
def sample_data():
    """Create sample data for testing."""
    np.random.seed(42)
    n_samples = 100
    n_features = 5
    
    # Generate features with some correlation
    X = np.random.randn(n_samples, n_features)
    # Add some structure
    X[:, 0] = X[:, 0] * 2 + np.random.randn(n_samples) * 0.5
    X[:, 1] = X[:, 0] * 0.5 + np.random.randn(n_samples) * 0.5
    
    # Generate target with relationship to first feature
    y = X[:, 0] * 2 + X[:, 1] * 0.5 + np.random.randn(n_samples) * 0.1
    
    return X, y, [f"feature_{i}" for i in range(n_features)]

def test_permutation_importance_basic(sample_data):
    """Test that permutation importance returns non-empty results."""
    X, y, feature_names = sample_data
    
    importance = calculate_permutation_importance(X, y, n_repeats=3, random_state=42)
    
    assert isinstance(importance, dict)
    assert len(importance) == len(feature_names)
    
    for feat_key, scores in importance.items():
        assert isinstance(scores, list)
        assert len(scores) == 3  # n_repeats
        # Scores should be numeric
        for s in scores:
            assert isinstance(s, (int, float))

def test_permutation_importance_stability(sample_data):
    """Test that importance scores are stable across runs."""
    X, y, feature_names = sample_data
    
    importance1 = calculate_permutation_importance(X, y, n_repeats=5, random_state=42)
    importance2 = calculate_permutation_importance(X, y, n_repeats=5, random_state=42)
    
    # Results should be identical with same seed
    for feat_key in importance1:
        assert importance1[feat_key] == importance2[feat_key]

def test_permutation_importance_feature_ranking(sample_data):
    """Test that important features have higher importance scores."""
    X, y, feature_names = sample_data
    
    # Feature 0 has strongest relationship with y
    importance = calculate_permutation_importance(X, y, n_repeats=10, random_state=42)
    
    mean_importance = {k: np.mean(v) for k, v in importance.items()}
    
    # Feature 0 should generally have higher importance than feature 2 or 3
    assert mean_importance["feature_0"] >= mean_importance["feature_2"]
    assert mean_importance["feature_0"] >= mean_importance["feature_3"]

def test_vif_calculation(sample_data):
    """Test VIF calculation returns valid values."""
    X, y, feature_names = sample_data
    
    vif_df = calculate_vif(X, feature_names)
    
    assert isinstance(vif_df, pd.DataFrame)
    assert "feature" in vif_df.columns
    assert "vif" in vif_df.columns
    assert len(vif_df) == len(feature_names)
    
    # VIF should be >= 1.0
    assert all(vif_df["vif"] >= 1.0)

def test_vif_high_correlation():
    """Test VIF detects high correlation."""
    np.random.seed(42)
    n = 50
    
    # Create highly correlated features
    x1 = np.random.randn(n)
    x2 = x1 * 0.95 + np.random.randn(n) * 0.1  # High correlation
    x3 = np.random.randn(n)
    
    X = np.column_stack([x1, x2, x3])
    feature_names = ["x1", "x2", "x3"]
    
    vif_df = calculate_vif(X, feature_names)
    
    # x1 and x2 should have high VIF
    x1_vif = vif_df[vif_df["feature"] == "x1"]["vif"].values[0]
    x2_vif = vif_df[vif_df["feature"] == "x2"]["vif"].values[0]
    
    assert x1_vif > 5.0  # Should be elevated
    assert x2_vif > 5.0

def test_median_split_sensitivity(sample_data):
    """Test median-split sensitivity analysis."""
    X, y, feature_names = sample_data
    
    result_df = run_median_split_sensitivity(X, y, feature_names, top_k=2)
    
    assert isinstance(result_df, pd.DataFrame)
    assert "threshold" in result_df.columns
    assert "feature" in result_df.columns
    assert "cohens_d" in result_df.columns
    assert "p_value" in result_df.columns
    
    # Should have results for multiple thresholds
    assert len(result_df) > 0

def test_regularization_sensitivity(sample_data):
    """Test regularization sensitivity analysis."""
    X, y, feature_names = sample_data
    
    result_df = run_regularization_sensitivity(X, y)
    
    assert isinstance(result_df, pd.DataFrame)
    assert "alpha" in result_df.columns
    assert "r_squared" in result_df.columns
    assert "converged" in result_df.columns
    
    # Should have results for multiple alphas
    assert len(result_df) > 0
    
    # R-squared should be between -inf and 1.0
    assert all(result_df["r_squared"] <= 1.0)

def test_regularization_sensitivity_alpha_zero(sample_data):
    """Test that alpha=0 gives reasonable results."""
    X, y, feature_names = sample_data
    
    result_df = run_regularization_sensitivity(X, y, alphas=[0.0, 0.5, 1.0])
    
    alpha_zero_row = result_df[result_df["alpha"] == 0.0]
    assert len(alpha_zero_row) == 1
    
    # alpha=0 is OLS, should converge
    assert alpha_zero_row["converged"].values[0]

def test_permutation_importance_empty_input():
    """Test error handling for empty input."""
    X = np.array([]).reshape(0, 5)
    y = np.array([])
    
    with pytest.raises(ValueError):
        calculate_permutation_importance(X, y)

def test_vif_small_sample():
    """Test VIF with small sample size (warning expected)."""
    np.random.seed(42)
    X = np.random.randn(10, 3)
    feature_names = ["f1", "f2", "f3"]
    
    # Should not raise, but may warn
    vif_df = calculate_vif(X, feature_names)
    assert isinstance(vif_df, pd.DataFrame)
    assert len(vif_df) == 3