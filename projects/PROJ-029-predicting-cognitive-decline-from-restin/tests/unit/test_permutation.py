"""
Unit tests for p-value calculation logic.
"""
import pytest
import numpy as np

def test_p_value_calculation():
    """Test p-value calculation from permutation distribution."""
    # Observed statistic
    observed = 0.75
    
    # Permutation distribution (random stats)
    perm_stats = np.array([0.4, 0.5, 0.6, 0.55, 0.45, 0.5, 0.6, 0.5, 0.4, 0.55])
    
    # Count how many permuted stats are >= observed
    count = np.sum(perm_stats >= observed)
    p_value = count / len(perm_stats)
    
    # Since observed (0.75) is higher than all perm_stats, p_value should be 0.0
    assert p_value == 0.0

def test_p_value_calculation_low_observed():
    """Test p-value when observed is low."""
    observed = 0.4
    perm_stats = np.array([0.4, 0.5, 0.6, 0.55, 0.45, 0.5, 0.6, 0.5, 0.4, 0.55])
    
    count = np.sum(perm_stats >= observed)
    p_value = count / len(perm_stats)
    
    # All 10 values are >= 0.4
    assert p_value == 1.0
