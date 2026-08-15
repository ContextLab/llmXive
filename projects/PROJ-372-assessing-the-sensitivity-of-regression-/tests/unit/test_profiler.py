"""
Unit tests for the profiler module.
"""
import pytest
import pandas as pd
import numpy as np
from src.ingestion.profiler import (
    profile_dataset,
    compute_condition_number,
    compute_breusch_pagan,
    compute_cooks_distance,
    classify_condition_number,
    classify_breusch_pagan,
    classify_cooks
)
from src.models.data_models import ViolationSeverity

def test_profile_dataset_basic():
    """Test basic profiling on a simple synthetic dataset."""
    np.random.seed(42)
    n = 100
    X1 = np.random.normal(0, 1, n)
    X2 = np.random.normal(0, 1, n)
    y = 2 * X1 + 3 * X2 + np.random.normal(0, 0.1, n)
    
    df = pd.DataFrame({'y': y, 'x1': X1, 'x2': X2})
    
    profile = profile_dataset(df, 'y', ['x1', 'x2'])
    
    assert profile.n_observations == n
    assert profile.n_features == 2
    assert profile.condition_number > 0
    assert not np.isnan(profile.breusch_pagan_stat)
    assert not np.isnan(profile.max_cooks_distance)
    assert isinstance(profile.overall_violation_severity, ViolationSeverity)

def test_classify_condition_number():
    """Test severity classification for condition number."""
    assert classify_condition_number(10) == ViolationSeverity.LOW
    assert classify_condition_number(50) == ViolationSeverity.MEDIUM
    assert classify_condition_number(200) == ViolationSeverity.HIGH
    assert classify_condition_number(float('inf')) == ViolationSeverity.HIGH

def test_classify_breusch_pagan():
    """Test severity classification for BP p-value."""
    assert classify_breusch_pagan(0.6) == ViolationSeverity.LOW
    assert classify_breusch_pagan(0.03) == ViolationSeverity.MEDIUM
    assert classify_breusch_pagan(0.001) == ViolationSeverity.HIGH
    assert classify_breusch_pagan(float('nan')) == ViolationSeverity.LOW

def test_classify_cooks():
    """Test severity classification for Cook's Distance."""
    n = 100
    assert classify_cooks(0.001, n) == ViolationSeverity.LOW
    assert classify_cooks(0.1, n) == ViolationSeverity.MEDIUM
    assert classify_cooks(2.0, n) == ViolationSeverity.HIGH

def test_profile_dataset_nan_handling():
    """Test that profile_dataset handles NaNs correctly."""
    df = pd.DataFrame({
        'y': [1.0, 2.0, np.nan, 4.0],
        'x1': [1.0, np.nan, 3.0, 4.0],
        'x2': [1.0, 2.0, 3.0, 4.0]
    })
    
    profile = profile_dataset(df, 'y', ['x1', 'x2'])
    
    # Should have 2 valid rows (index 3 and maybe 0/1/2 depending on mask)
    # Actually: row 0 (x1 ok, y ok), row 1 (x1 nan), row 2 (y nan), row 3 (ok)
    # Mask: row 0 (ok), row 1 (fail), row 2 (fail), row 3 (ok) -> 2 rows
    assert profile.n_observations == 2
    assert profile.n_features == 2

def test_profile_dataset_singular_matrix():
    """Test handling of perfect multicollinearity."""
    n = 100
    X1 = np.random.normal(0, 1, n)
    X2 = X1 * 2.0  # Perfectly collinear
    y = X1 + np.random.normal(0, 0.1, n)
    
    df = pd.DataFrame({'y': y, 'x1': X1, 'x2': X2})
    
    profile = profile_dataset(df, 'y', ['x1', 'x2'])
    
    assert profile.condition_number == float('inf')
    assert profile.condition_number_severity == ViolationSeverity.HIGH

def test_profile_dataset_empty_features():
    """Test that empty feature list raises error."""
    df = pd.DataFrame({'y': [1, 2, 3], 'x': [1, 2, 3]})
    with pytest.raises(ValueError, match="No feature columns"):
        profile_dataset(df, 'y', [])