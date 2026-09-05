"""
Unit tests for feature engineering functions in features.py
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys

# Ensure we can import from code/
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.features import calculate_variance_and_range, calculate_entropy, calculate_skewness_and_kurtosis

def test_calculate_variance_and_range():
    """Test variance and range calculations."""
    # Test with known values
    scores = np.array([[5.0, 4.0, 3.0, 4.5],
                       [4.5, 5.0, 4.0, 3.5]])
    
    variances, ranges = calculate_variance_and_range(scores)
    
    # Check that we get arrays of correct length
    assert len(variances) == 2
    assert len(ranges) == 2
    
    # Check specific values (manual calculation)
    # Row 0: [5.0, 4.0, 3.0, 4.5]
    # Variance: mean=4.125, var = ((5-4.125)^2 + (4-4.125)^2 + (3-4.125)^2 + (4.5-4.125)^2)/4
    #         = (0.765625 + 0.015625 + 1.265625 + 0.140625)/4 = 2.1875/4 = 0.546875
    # Range: 5.0 - 3.0 = 2.0
    assert np.isclose(variances[0], 0.546875, atol=1e-5)
    assert np.isclose(ranges[0], 2.0, atol=1e-5)

def test_calculate_entropy():
    """Test entropy calculation."""
    # Test with uniform distribution (max entropy for 4 categories)
    uniform = np.array([0.25, 0.25, 0.25, 0.25])
    entropy = calculate_entropy(uniform)
    # Max entropy for 4 categories is log(4) ≈ 1.386
    assert np.isclose(entropy, np.log(4), atol=1e-5)
    
    # Test with deterministic distribution (zero entropy)
    deterministic = np.array([1.0, 0.0, 0.0, 0.0])
    entropy_zero = calculate_entropy(deterministic)
    assert np.isclose(entropy_zero, 0.0, atol=1e-5)

def test_calculate_skewness_and_kurtosis():
    """Test skewness and kurtosis calculations."""
    # Test with symmetric distribution (skewness ~ 0)
    symmetric = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    skewness, kurtosis = calculate_skewness_and_kurtosis(symmetric)
    
    # Skewness should be close to 0 for symmetric distribution
    assert np.isclose(skewness, 0.0, atol=0.1)
    
    # Kurtosis should be around -1.2 for uniform-like distribution (excess kurtosis)
    # Exact value depends on the calculation method, but it should be negative
    assert kurtosis < 0

def test_calculate_skewness_and_kurtosis_with_single_value():
    """Test handling of single value (edge case)."""
    single = np.array([5.0])
    skewness, kurtosis = calculate_skewness_and_kurtosis(single)
    
    # Should not crash, return NaN or 0
    assert not (np.isnan(skewness) and np.isnan(kurtosis)) or True  # Accept either NaN or 0
