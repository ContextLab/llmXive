"""
Unit tests for edge cases in data generation.
"""
import pytest
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data_generation.utils import apply_epsilon_floor, safe_log


def test_extreme_values():
    """Test handling of extreme numerical values."""
    epsilon = 1e-6
    
    # Very large value
    result = apply_epsilon_floor(1e10, epsilon)
    assert result == 1e10
    
    # Very small positive value
    result = apply_epsilon_floor(1e-20, epsilon)
    assert result == epsilon
    
    # Negative value
    result = apply_epsilon_floor(-1e10, epsilon)
    assert result == epsilon


def test_nan_handling():
    """Test that NaN values are handled correctly."""
    # safe_log should handle NaN by returning a safe value or raising
    # For this test, we assume it returns a safe value (epsilon log)
    result = safe_log(np.nan)
    # Should not be NaN
    assert not np.isnan(result)
    
    result = safe_log(np.inf)
    # Should be a finite number
    assert np.isfinite(result)
