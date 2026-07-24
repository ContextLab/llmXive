"""
Unit tests for Cohen's d calculation and statistical analysis utilities.

This module verifies the correctness of statistical computations used in
the analysis of cache line padding impact on false sharing.
"""

import pytest
import math
import sys
from pathlib import Path

# Add project root to path to allow imports from code/analysis
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.analysis.statistics_utils import cohens_d, two_sample_ttest


class TestCohensD:
    """Tests for Cohen's d effect size calculation."""

    def test_identical_groups_returns_zero(self):
        """Cohen's d should be 0 when both groups have identical means and variances."""
        group1 = [10.0, 10.0, 10.0, 10.0, 10.0]
        group2 = [10.0, 10.0, 10.0, 10.0, 10.0]
        
        d = cohens_d(group1, group2)
        assert math.isclose(d, 0.0, abs_tol=1e-9)

    def test_simple_known_values(self):
        """Test with manually calculated values."""
        # Group 1: mean=5, var=2.5, n=5
        # Group 2: mean=7, var=2.5, n=5
        # Pooled std = sqrt((2.5 + 2.5)/2) = sqrt(2.5) ≈ 1.5811
        # Cohen's d = (7 - 5) / 1.5811 ≈ 1.2649
        group1 = [3.0, 5.0, 5.0, 5.0, 7.0]  # mean=5, var=2.5
        group2 = [5.0, 7.0, 7.0, 7.0, 9.0]  # mean=7, var=2.5
        
        d = cohens_d(group1, group2)
        expected = 2.0 / math.sqrt(2.5)
        assert math.isclose(d, expected, rel_tol=1e-4)

    def test_negative_cohens_d(self):
        """Cohen's d should be negative when group1 mean < group2 mean."""
        group1 = [1.0, 2.0, 3.0]
        group2 = [10.0, 11.0, 12.0]
        
        d = cohens_d(group1, group2)
        assert d < 0

    def test_positive_cohens_d(self):
        """Cohen's d should be positive when group1 mean > group2 mean."""
        group1 = [10.0, 11.0, 12.0]
        group2 = [1.0, 2.0, 3.0]
        
        d = cohens_d(group1, group2)
        assert d > 0

    def test_large_sample_sizes(self):
        """Test with larger sample sizes to ensure numerical stability."""
        group1 = [i * 0.1 for i in range(1000)]
        group2 = [i * 0.1 + 5.0 for i in range(1000)]
        
        d = cohens_d(group1, group2)
        # Should be approximately 5.0 / 0.0577 ≈ 86.6
        assert d > 50.0

    def test_single_element_groups(self):
        """Test behavior with single element groups (variance will be 0)."""
        group1 = [5.0]
        group2 = [10.0]
        
        # When variance is 0, pooled std is 0, leading to division by zero
        # The function should handle this gracefully (return inf or raise)
        with pytest.raises((ZeroDivisionError, ValueError)):
            cohens_d(group1, group2)

    def test_unequal_sample_sizes(self):
        """Test with groups of different sizes."""
        group1 = [1.0, 2.0, 3.0, 4.0, 5.0]
        group2 = [10.0, 11.0]
        
        d = cohens_d(group1, group2)
        assert not math.isnan(d)
        assert not math.isinf(d)

    def test_float_precision(self):
        """Test with high precision floating point values."""
        group1 = [0.123456789, 0.234567890, 0.345678901]
        group2 = [0.987654321, 0.876543210, 0.765432109]
        
        d = cohens_d(group1, group2)
        assert not math.isnan(d)
        assert not math.isinf(d)

    def test_magnitude_interpretation(self):
        """Test that Cohen's d magnitudes align with conventional thresholds."""
        # Small effect (d ≈ 0.2)
        group1 = [0.0] * 100
        group2 = [0.2] * 100
        d_small = cohens_d(group1, group2)
        assert abs(d_small) < 0.5  # Should be small

        # Large effect (d ≈ 0.8)
        group1 = [0.0] * 100
        group2 = [1.0] * 100
        d_large = cohens_d(group1, group2)
        assert abs(d_large) > 0.5  # Should be larger


class TestTwoSampleTTest:
    """Tests for two-sample t-test calculation."""

    def test_identical_groups_high_p_value(self):
        """Identical groups should yield a high p-value (fail to reject null)."""
        group1 = [10.0] * 20
        group2 = [10.0] * 20
        
        t_stat, p_value = two_sample_ttest(group1, group2)
        assert p_value > 0.05

    def test_different_groups_low_p_value(self):
        """Clearly different groups should yield a low p-value."""
        group1 = [1.0] * 50
        group2 = [100.0] * 50
        
        t_stat, p_value = two_sample_ttest(group1, group2)
        assert p_value < 0.001

    def test_t_statistic_sign(self):
        """T-statistic sign should match the direction of difference."""
        group1 = [1.0, 2.0, 3.0]
        group2 = [10.0, 11.0, 12.0]
        
        t_stat, _ = two_sample_ttest(group1, group2)
        assert t_stat < 0  # group1 < group2

        t_stat, _ = two_sample_ttest(group2, group1)
        assert t_stat > 0  # group1 > group2

    def test_return_values(self):
        """Ensure function returns valid numeric types."""
        group1 = [1.0, 2.0, 3.0]
        group2 = [4.0, 5.0, 6.0]
        
        t_stat, p_value = two_sample_ttest(group1, group2)
        
        assert isinstance(t_stat, float)
        assert isinstance(p_value, float)
        assert not math.isnan(t_stat)
        assert not math.isnan(p_value)
        assert 0.0 <= p_value <= 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
