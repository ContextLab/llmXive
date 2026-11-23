"""
Unit tests for multicollinearity check in regression module.
"""
import pytest
import numpy as np
from regression import check_multicollinearity, RegressionError

def test_vif_perfect_collinearity():
    """Test VIF calculation with perfect collinearity (should be very high)."""
    # Create perfectly collinear data: x2 = 2 * x1
    X = np.column_stack([
        np.array([1.0, 2.0, 3.0, 4.0, 5.0]),
        np.array([2.0, 4.0, 6.0, 8.0, 10.0])  # Perfectly collinear
    ])
    feature_names = ['x1', 'x2']
    
    result = check_multicollinearity(X, feature_names)
    
    # VIF should be very high (or infinite) for perfect collinearity
    assert result['max_vif'] >= 5.0, "VIF should be high for perfect collinearity"
    assert result['is_stable'] == False, "Model should be unstable with perfect collinearity"

def test_vif_independent_predictors():
    """Test VIF calculation with independent predictors (should be low)."""
    # Create independent data
    np.random.seed(42)
    X = np.column_stack([
        np.random.normal(0, 1, 100),
        np.random.normal(0, 1, 100)
    ])
    feature_names = ['x1', 'x2']
    
    result = check_multicollinearity(X, feature_names)
    
    # VIF should be close to 1 for independent predictors
    assert result['max_vif'] < 5.0, "VIF should be low for independent predictors"
    assert result['is_stable'] == True, "Model should be stable with independent predictors"
    assert 'x1' in result['vif_values']
    assert 'x2' in result['vif_values']

def test_vif_threshold_custom():
    """Test VIF with custom threshold."""
    np.random.seed(42)
    X = np.column_stack([
        np.random.normal(0, 1, 100),
        np.random.normal(0, 1, 100) + 0.5 * np.random.normal(0, 1, 100)  # Some correlation
    ])
    feature_names = ['x1', 'x2']
    
    # With default threshold (5.0)
    result_default = check_multicollinearity(X, feature_names, threshold=5.0)
    
    # With very low threshold
    result_low = check_multicollinearity(X, feature_names, threshold=1.5)
    
    # The low threshold should flag instability if VIF > 1.5
    if result_low['max_vif'] > 1.5:
        assert result_low['is_stable'] == False
    else:
        assert result_low['is_stable'] == True

def test_vif_single_predictor():
    """Test VIF with single predictor (should warn and return stable)."""
    X = np.array([1.0, 2.0, 3.0, 4.0, 5.0]).reshape(-1, 1)
    feature_names = ['x1']
    
    result = check_multicollinearity(X, feature_names)
    
    assert result['max_vif'] == 0.0
    assert result['is_stable'] == True
    assert 'warning' in result

def test_vif_warning_message():
    """Test that warning message is included when VIF exceeds threshold."""
    # Create highly correlated data
    np.random.seed(42)
    x1 = np.random.normal(0, 1, 50)
    x2 = x1 + np.random.normal(0, 0.1, 50)  # Highly correlated
    X = np.column_stack([x1, x2])
    feature_names = ['x1', 'x2']
    
    result = check_multicollinearity(X, feature_names, threshold=5.0)
    
    if not result['is_stable']:
        assert 'warning' in result
        assert 'Multicollinearity' in result['warning']