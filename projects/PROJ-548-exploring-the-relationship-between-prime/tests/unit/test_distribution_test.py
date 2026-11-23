import pytest
import math
import os
import sys
import tempfile
from pathlib import Path
import numpy as np

# Import the module under test
from src.analysis.distribution_test import gue_extreme_value_cdf, pair_correlation_distribution, compute_empirical_cdf

class TestGUEExtremeValueCDF:
    """Tests for the GUE Extreme Value CDF (Tracy-Widom) implementation."""

    def test_gue_cdf_monotonicity(self):
        """The CDF must be non-decreasing."""
        x_vals = np.linspace(-5, 5, 50)
        cdf_vals = [gue_extreme_value_cdf(x) for x in x_vals]
        
        for i in range(1, len(cdf_vals)):
            assert cdf_vals[i] >= cdf_vals[i-1] - 1e-10, "CDF is not monotonic"

    def test_gue_cdf_bounds(self):
        """The CDF must be between 0 and 1."""
        x_vals = np.linspace(-10, 10, 100)
        cdf_vals = [gue_extreme_value_cdf(x) for x in x_vals]
        
        for val in cdf_vals:
            assert 0.0 <= val <= 1.0, f"CDF value {val} out of bounds"

    def test_gue_cdf_limits(self):
        """CDF should approach 0 at -inf and 1 at +inf."""
        # Check extreme negative
        assert gue_extreme_value_cdf(-10) < 0.001
        # Check extreme positive
        assert gue_extreme_value_cdf(10) > 0.999

    def test_gue_cdf_median_approx(self):
        """The median of Tracy-Widom beta=2 is approximately -0.17."""
        # We check if the CDF at -0.17 is close to 0.5
        median_approx = -0.17
        val = gue_extreme_value_cdf(median_approx)
        # Allow some tolerance
        assert 0.4 < val < 0.6, f"Median check failed: CDF({median_approx}) = {val}"

class TestPairCorrelationDistribution:
    """Tests for the pair correlation function."""

    def test_pair_correlation_at_zero(self):
        """At x=0, the pair correlation should be 0 (repulsion)."""
        assert pair_correlation_distribution(0.0) == 0.0

    def test_pair_correlation_at_large(self):
        """At large x, the pair correlation should approach 1 (independence)."""
        val = pair_correlation_distribution(10.0)
        assert abs(val - 1.0) < 0.01

    def test_pair_correlation_positive(self):
        """The function should be non-negative."""
        x_vals = np.linspace(0, 20, 100)
        for x in x_vals:
            assert pair_correlation_distribution(x) >= -1e-10

class TestComputeEmpiricalCDF:
    """Tests for empirical CDF calculation."""

    def test_empirical_cdf_basic(self):
        """Test basic CDF computation."""
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        sorted_data, cdf_vals = compute_empirical_cdf(data)
        
        assert len(sorted_data) == 5
        assert len(cdf_vals) == 5
        assert sorted_data == data  # Already sorted
        # CDF values should be 1/5, 2/5, ...
        expected_cdf = [0.2, 0.4, 0.6, 0.8, 1.0]
        for i, val in enumerate(cdf_vals):
            assert abs(val - expected_cdf[i]) < 1e-10

    def test_empirical_cdf_unsorted(self):
        """Test CDF computation on unsorted data."""
        data = [3.0, 1.0, 5.0, 2.0, 4.0]
        sorted_data, cdf_vals = compute_empirical_cdf(data)
        
        assert sorted_data == [1.0, 2.0, 3.0, 4.0, 5.0]
        assert cdf_vals == [0.2, 0.4, 0.6, 0.8, 1.0]

    def test_empirical_cdf_empty(self):
        """Test CDF computation on empty data."""
        sorted_data, cdf_vals = compute_empirical_cdf([])
        assert sorted_data == []
        assert cdf_vals == []
