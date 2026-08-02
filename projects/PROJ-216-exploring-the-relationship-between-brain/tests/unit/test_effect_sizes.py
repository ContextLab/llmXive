"""
Unit tests for effect size calculations in calculate_effect_sizes.py
"""
import pytest
import numpy as np
from code.calculate_effect_sizes import calculate_cohen_d, calculate_ci_95_cohen_d

class TestCohenD:
    def test_basic_cohen_d(self):
        """Test basic Cohen's d calculation."""
        group1 = np.array([2.0, 4.0, 6.0])
        group2 = np.array([1.0, 3.0, 5.0])
        # Mean1=4, Mean2=3. Diff=1.
        # Std1=sqrt(2), Std2=sqrt(2). Pooled=sqrt(2).
        # d = 1 / sqrt(2) ≈ 0.707
        d = calculate_cohen_d(group1, group2)
        assert abs(d - 0.7071) < 0.001

    def test_identical_groups(self):
        """Cohen's d should be 0 for identical groups."""
        group1 = np.array([1.0, 2.0, 3.0])
        group2 = np.array([1.0, 2.0, 3.0])
        d = calculate_cohen_d(group1, group2)
        assert d == 0.0

    def test_insufficient_data(self):
        """Should return 0.0 for insufficient data."""
        group1 = np.array([1.0])
        group2 = np.array([2.0, 3.0])
        d = calculate_cohen_d(group1, group2)
        assert d == 0.0

class TestCI95:
    def test_ci_calculation(self):
        """Test 95% CI calculation."""
        d = 0.5
        n1, n2 = 20, 20
        lower, upper = calculate_ci_95_cohen_d(d, n1, n2)
        # Just check that lower < d < upper
        assert lower < d < upper
        # Check reasonable magnitude
        assert abs(lower) < 2.0 and abs(upper) < 2.0

    def test_small_sample_ci(self):
        """Test CI with small sample size."""
        d = 0.5
        n1, n2 = 3, 3
        lower, upper = calculate_ci_95_cohen_d(d, n1, n2)
        # CI should be wider with small samples
        assert (upper - lower) > (1.0 - 0.0) # Rough check