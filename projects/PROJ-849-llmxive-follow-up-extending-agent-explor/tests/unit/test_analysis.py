"""
Unit tests for analysis service functions.
"""
import pytest
import numpy as np
from scipy.stats import pearsonr
from services.analysis_service import compute_pearson_correlation, validate_sample_size

def test_validate_sample_size_sufficient():
    """Test validation with sufficient sample size."""
    assert validate_sample_size(50) is True
    assert validate_sample_size(30) is True

def test_validate_sample_size_insufficient():
    """Test validation with insufficient sample size."""
    with pytest.raises(ValueError, match="Insufficient Sample Size"):
        validate_sample_size(29)
    
    with pytest.raises(ValueError, match="Insufficient Sample Size"):
        validate_sample_size(10)

def test_compute_pearson_correlation_negative():
    """Test Pearson correlation with negative correlation."""
    x = [1, 2, 3, 4, 5]
    y = [5, 4, 3, 2, 1]
    
    correlation, p_value = compute_pearson_correlation(x, y)
    
    assert correlation < 0
    assert p_value < 1.0

def test_compute_pearson_correlation_positive():
    """Test Pearson correlation with positive correlation."""
    x = [1, 2, 3, 4, 5]
    y = [1, 2, 3, 4, 5]
    
    correlation, p_value = compute_pearson_correlation(x, y)
    
    assert correlation > 0
    assert p_value < 1.0

def test_compute_pearson_correlation_random():
    """Test Pearson correlation with random data."""
    np.random.seed(42)
    x = np.random.randn(50)
    y = np.random.randn(50)
    
    correlation, p_value = compute_pearson_correlation(x.tolist(), y.tolist())
    
    # Random data should have low correlation
    assert abs(correlation) < 0.5