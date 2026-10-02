import pytest
import numpy as np
from analysis import create_binary_indicator_map, calculate_moran_i, calculate_statistical_power

def test_create_binary_indicator_map():
    """Test that binary map is created correctly."""
    data = np.array([[1, 2, 3], [4, 1, 2], [1, 1, 4]])
    binary = create_binary_indicator_map(data, target_class_id=1)
    expected = np.array([[1, 0, 0], [0, 1, 0], [1, 1, 0]])
    assert np.array_equal(binary, expected)

def test_calculate_statistical_power():
    """Test power calculation logic."""
    # H0 distribution centered around 0
    h0 = [0.1, 0.2, 0.3, 0.4, 0.5]
    # H1 distribution shifted higher
    h1 = [0.6, 0.7, 0.8, 0.9, 1.0]
    
    # Critical value at 95% of H0 is 0.5
    # All H1 values > 0.5, so power should be 1.0
    power = calculate_statistical_power(h0, h1, alpha=0.05)
    assert power == 1.0

def test_calculate_statistical_power_zero_h1():
    """Test power calculation when no H1 rejections."""
    h0 = [0.1, 0.2, 0.3, 0.4, 0.5]
    h1 = [0.1, 0.2, 0.3] # All below critical value
    
    power = calculate_statistical_power(h0, h1, alpha=0.05)
    assert power == 0.0
