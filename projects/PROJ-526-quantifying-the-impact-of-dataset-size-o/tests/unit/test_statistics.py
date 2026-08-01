"""
Unit Test: Statistical Analysis (Permutation Test)
"""
import numpy as np
from code.analyze_physics import permutation_test

def test_permutation_test_basic():
    """Test basic permutation test functionality."""
    # Two small groups (N=2-3 as per amendment)
    group_a = np.array([0.45, 0.50, 0.48])
    group_b = np.array([0.35, 0.38, 0.36])

    p_value = permutation_test(group_a, group_b, n_permutations=1000)

    assert 0.0 <= p_value <= 1.0, "p-value must be between 0 and 1"
    assert isinstance(p_value, float), "p-value must be a float"

def test_permutation_test_identical_groups():
    """Test that identical groups yield high p-value."""
    group = np.array([0.4, 0.5, 0.45])
    p_value = permutation_test(group, group, n_permutations=100)
    assert p_value > 0.05, "Identical groups should not be significant"
