"""
Unit tests for diagnostics module.
"""
import pytest
import pandas as pd
import numpy as np
from code.diagnostics import check_leakage, calculate_vif

def test_check_leakage_no_leakage():
    """
    Test that a feature with high importance results in a high drop (no leakage).
    We create a dataset where 'feature_a' is strongly correlated with target.
    Removing it should cause a large MAE drop (> 0.10).
    """
    np.random.seed(42)
    n = 100
    # Create a strong feature
    feature_a = np.random.rand(n)
    # Target is mostly determined by feature_a
    target = 2 * feature_a + np.random.normal(0, 0.1, n)
    
    # Create a weak feature
    feature_b = np.random.rand(n)
    
    df = pd.DataFrame({
        'feature_a': feature_a,
        'feature_b': feature_b,
        'weibull_modulus': target
    })
    
    result = check_leakage(df, feature_col='feature_a', target_col='weibull_modulus')
    
    assert result['leakage_status'] == 'No Significant Leakage', \
        f"Expected 'No Significant Leakage' but got {result['leakage_status']}"
    assert result['performance_drop'] > 0.10, \
        f"Expected drop > 0.10 but got {result['performance_drop']}"

def test_check_leakage_potential_leakage():
    """
    Test that a feature with low importance results in a low drop (potential leakage).
    We create a dataset where 'feature_a' has no correlation with target.
    Removing it should cause almost no drop (< 0.10).
    """
    np.random.seed(42)
    n = 100
    # Create a feature with no relation to target
    feature_a = np.random.rand(n)
    # Target is determined by feature_b
    feature_b = np.random.rand(n)
    target = 2 * feature_b + np.random.normal(0, 0.1, n)
    
    df = pd.DataFrame({
        'feature_a': feature_a,
        'feature_b': feature_b,
        'weibull_modulus': target
    })
    
    result = check_leakage(df, feature_col='feature_a', target_col='weibull_modulus')
    
    assert result['leakage_status'] == 'Potential Leakage Detected', \
        f"Expected 'Potential Leakage Detected' but got {result['leakage_status']}"
    assert result['performance_drop'] < 0.10, \
        f"Expected drop < 0.10 but got {result['performance_drop']}"

def test_check_leakage_missing_feature():
    """
    Test behavior when the feature_col is not in the dataframe.
    """
    np.random.seed(42)
    n = 100
    df = pd.DataFrame({
        'feature_a': np.random.rand(n),
        'weibull_modulus': np.random.rand(n)
    })
    
    # Should handle missing feature gracefully (drop=0, potential leakage)
    result = check_leakage(df, feature_col='non_existent', target_col='weibull_modulus')
    
    assert result['leakage_status'] == 'Potential Leakage Detected'
    assert result['performance_drop'] == 0.0

def test_calculate_vif_basic():
    """
    Test basic VIF calculation on uncorrelated features.
    VIF should be close to 1.0 for uncorrelated features.
    """
    np.random.seed(42)
    n = 100
    # Create uncorrelated features
    df = pd.DataFrame({
        'feature_a': np.random.rand(n),
        'feature_b': np.random.rand(n),
        'feature_c': np.random.rand(n)
    })
    
    vif_result = calculate_vif(df)
    
    assert isinstance(vif_result, dict)
    assert 'feature_a' in vif_result
    assert 'feature_b' in vif_result
    assert 'feature_c' in vif_result
    
    # VIF for uncorrelated features should be close to 1
    for feature, vif in vif_result.items():
        assert 0.9 < vif < 1.5, f"Expected VIF ~1.0 for {feature}, got {vif}"

def test_calculate_vif_high_correlation():
    """
    Test VIF calculation with highly correlated features.
    VIF should be significantly > 5.0 for correlated features.
    """
    np.random.seed(42)
    n = 100
    base = np.random.rand(n)
    # Create highly correlated features
    df = pd.DataFrame({
        'feature_a': base,
        'feature_b': base + np.random.normal(0, 0.01, n),  # Highly correlated
        'feature_c': np.random.rand(n)  # Uncorrelated
    })
    
    vif_result = calculate_vif(df)
    
    assert isinstance(vif_result, dict)
    # feature_a and feature_b should have high VIF
    assert vif_result['feature_a'] > 5.0, f"Expected high VIF for feature_a, got {vif_result['feature_a']}"
    assert vif_result['feature_b'] > 5.0, f"Expected high VIF for feature_b, got {vif_result['feature_b']}"
    # feature_c should have low VIF
    assert vif_result['feature_c'] < 2.0, f"Expected low VIF for feature_c, got {vif_result['feature_c']}"

def test_calculate_vif_single_feature():
    """
    Test VIF calculation with a single feature (should be 1.0).
    """
    np.random.seed(42)
    n = 100
    df = pd.DataFrame({
        'feature_a': np.random.rand(n)
    })
    
    vif_result = calculate_vif(df)
    
    assert isinstance(vif_result, dict)
    assert 'feature_a' in vif_result
    # Single feature VIF should be 1.0
    assert vif_result['feature_a'] == 1.0

def test_calculate_vif_empty_dataframe():
    """
    Test VIF calculation with an empty dataframe.
    Should handle gracefully.
    """
    df = pd.DataFrame()
    
    vif_result = calculate_vif(df)
    
    assert isinstance(vif_result, dict)
    assert len(vif_result) == 0

def test_calculate_vif_constant_feature():
    """
    Test VIF calculation with a constant feature (should handle division by zero).
    """
    np.random.seed(42)
    n = 100
    df = pd.DataFrame({
        'feature_a': np.ones(n),  # Constant feature
        'feature_b': np.random.rand(n)
    })
    
    # This should not raise an exception
    vif_result = calculate_vif(df)
    
    assert isinstance(vif_result, dict)
    # Constant feature VIF might be NaN or very high, but should be present
    assert 'feature_a' in vif_result or 'feature_b' in vif_result