"""
Unit tests for statistics utilities.
"""
import pytest
import numpy as np
from utils.stats import calculate_correlation_matrix, calculate_feature_variance

def test_correlation_matrix():
    """Test correlation matrix calculation."""
    data = np.random.rand(100, 3)
    corr = calculate_correlation_matrix(data)
    
    assert corr.shape == (3, 3)
    assert np.isclose(corr[0, 0], 1.0)

def test_feature_variance():
    """Test feature variance calculation."""
    data = np.array([[1, 2, 3], [1, 2, 3], [1, 2, 3]]) # Zero variance
    var = calculate_feature_variance(data)
    
    assert np.all(var == 0.0)
    
    data2 = np.array([[1, 2], [2, 4], [3, 6]])
    var2 = calculate_feature_variance(data2)
    assert np.all(var2 > 0.0)
