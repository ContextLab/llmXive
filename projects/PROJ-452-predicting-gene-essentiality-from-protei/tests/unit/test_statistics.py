"""
test_statistics.py - Unit tests for the statistics module.
"""

import pytest
import numpy as np
from pathlib import Path
import json

from code.statistics import (
    calculate_spearman_correlation,
    fisher_z_transform,
    fisher_z_to_r,
    generate_null_distribution_permutation,
    calculate_empirical_p_value,
    benjamini_hochberg,
    StatisticsError
)

class TestSpearmanCorrelation:
    """Tests for calculate_spearman_correlation."""

    def test_basic_correlation(self):
        """Test basic Spearman correlation calculation."""
        x = [1, 2, 3, 4, 5]
        y = [2, 4, 6, 8, 10]
        corr, p_val = calculate_spearman_correlation(x, y)
        assert abs(corr - 1.0) < 0.001
        assert p_val < 0.05

    def test_negative_correlation(self):
        """Test negative correlation."""
        x = [1, 2, 3, 4, 5]
        y = [5, 4, 3, 2, 1]
        corr, p_val = calculate_spearman_correlation(x, y)
        assert abs(corr + 1.0) < 0.001

    def test_no_correlation(self):
        """Test zero correlation with random data."""
        np.random.seed(42)
        x = np.random.randn(100)
        y = np.random.randn(100)
        corr, p_val = calculate_spearman_correlation(x.tolist(), y.tolist())
        # With random data, correlation should be close to 0
        assert abs(corr) < 0.3

    def test_length_mismatch(self):
        """Test error on length mismatch."""
        with pytest.raises(StatisticsError):
            calculate_spearman_correlation([1, 2, 3], [1, 2])

    def test_insufficient_data(self):
        """Test error on insufficient data."""
        with pytest.raises(StatisticsError):
            calculate_spearman_correlation([1], [1])

    def test_zero_variance(self):
        """Test handling of zero variance."""
        x = [1, 1, 1, 1]
        y = [1, 2, 3, 4]
        corr, p_val = calculate_spearman_correlation(x, y)
        assert np.isnan(corr)

class TestFisherZTransform:
    """Tests for Fisher's z-transformation."""

    def test_transform_inverse(self):
        """Test that transform and inverse are consistent."""
        r = 0.5
        z = fisher_z_transform(r)
        r_back = fisher_z_to_r(z)
        assert abs(r - r_back) < 0.001

    def test_invalid_range(self):
        """Test error on invalid correlation range."""
        with pytest.raises(StatisticsError):
            fisher_z_transform(1.0)
        with pytest.raises(StatisticsError):
            fisher_z_transform(-1.0)

class TestNullDistribution:
    """Tests for null distribution generation."""

    def test_permutation_count(self):
        """Test that permutation generates correct number of samples."""
        np.random.seed(42)
        x = np.random.randn(50)
        y = np.random.randint(0, 2, 50)
        
        null_dist = generate_null_distribution_permutation(x.tolist(), y.tolist(), n_permutations=100, seed=42)
        assert len(null_dist) == 100

    def test_null_distribution_properties(self):
        """Test that null distribution is centered near zero."""
        np.random.seed(42)
        x = np.random.randn(100)
        y = np.random.randint(0, 2, 100)
        
        null_dist = generate_null_distribution_permutation(x.tolist(), y.tolist(), n_permutations=1000, seed=42)
        mean_corr = np.mean(null_dist)
        # With random data, null distribution should be centered near 0
        assert abs(mean_corr) < 0.2

class TestEmpiricalPValue:
    """Tests for empirical p-value calculation."""

    def test_extreme_observed(self):
        """Test p-value for extreme observed correlation."""
        null_dist = np.random.randn(1000) * 0.1  # Narrow distribution around 0
        observed = 2.0  # Very extreme
        p_val = calculate_empirical_p_value(observed, null_dist.tolist())
        assert p_val < 0.01

    def test_null_observed(self):
        """Test p-value when observed is at null mean."""
        null_dist = [0.0] * 1000
        observed = 0.0
        p_val = calculate_empirical_p_value(observed, null_dist)
        # Should be around 1.0 (or close to it)
        assert p_val > 0.9

    def test_empty_distribution(self):
        """Test error on empty null distribution."""
        with pytest.raises(StatisticsError):
            calculate_empirical_p_value(0.5, [])

    def test_nan_observed(self):
        """Test handling of NaN observed value."""
        null_dist = np.random.randn(100)
        p_val = calculate_empirical_p_value(np.nan, null_dist.tolist())
        assert np.isnan(p_val)

class TestBenjaminiHochberg:
    """Tests for BH correction."""

    def test_monotonicity(self):
        """Test that adjusted p-values are monotonic."""
        p_values = [0.01, 0.05, 0.03, 0.1, 0.02]
        adjusted = benjamini_hochberg(p_values)
        
        # After sorting original indices, adjusted should be non-decreasing
        sorted_indices = np.argsort(p_values)
        sorted_adjusted = [adjusted[i] for i in sorted_indices]
        
        for i in range(len(sorted_adjusted) - 1):
            assert sorted_adjusted[i] <= sorted_adjusted[i + 1] + 0.0001

    def test_cap_at_one(self):
        """Test that adjusted p-values don't exceed 1.0."""
        p_values = [0.9, 0.95, 0.99]
        adjusted = benjamini_hochberg(p_values)
        assert all(p <= 1.0 for p in adjusted)

    def test_empty_input(self):
        """Test handling of empty input."""
        assert benjamini_hochberg([]) == []