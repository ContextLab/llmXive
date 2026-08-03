"""
Unit tests for Mann-Whitney U test execution in code/analyze.py.

This module verifies that the Mann-Whitney U test is correctly executed
with proper handling of:
- Standard input data
- Empty groups
- Single element groups
- Effect size calculation (r)
"""

import pytest
import numpy as np
from scipy.stats import mannwhitneyu
from pathlib import Path
import sys

# Add project root to path to allow imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from analyze import run_mann_whitney_u, calculate_effect_size_r


class TestMannWhitneyUExecution:
    """Tests for the Mann-Whitney U test execution logic."""

    def test_basic_mwu_execution(self):
        """Test basic Mann-Whitney U test with standard data."""
        # Create sample data: AI group has lower turnaround times
        ai_group = [2.5, 3.1, 4.2, 5.0, 3.8]
        non_ai_group = [8.5, 9.2, 10.1, 11.3, 9.8, 12.0]

        result = run_mann_whitney_u(ai_group, non_ai_group)

        # Verify result structure
        assert "u_statistic" in result
        assert "p_value" in result
        assert "effect_size" in result
        assert "sample_sizes" in result

        # Verify sample sizes
        assert result["sample_sizes"]["ai"] == len(ai_group)
        assert result["sample_sizes"]["non_ai"] == len(non_ai_group)

        # Verify effect size is between 0 and 1
        assert 0 <= result["effect_size"] <= 1

        # Verify against scipy directly
        scipy_result = mannwhitneyu(ai_group, non_ai_group, alternative="two-sided")
        assert np.isclose(result["u_statistic"], scipy_result.statistic, rtol=1e-5)
        assert np.isclose(result["p_value"], scipy_result.pvalue, rtol=1e-5)

    def test_identical_groups(self):
        """Test when both groups have identical values."""
        ai_group = [5.0, 5.0, 5.0, 5.0]
        non_ai_group = [5.0, 5.0, 5.0, 5.0]

        result = run_mann_whitney_u(ai_group, non_ai_group)

        # With identical groups, p-value should be 1.0 (no difference)
        assert np.isclose(result["p_value"], 1.0, atol=1e-6)
        assert result["effect_size"] == 0.0

    def test_single_element_groups(self):
        """Test with single element in each group."""
        ai_group = [3.0]
        non_ai_group = [8.0]

        result = run_mann_whitney_u(ai_group, non_ai_group)

        # Should still produce valid results
        assert "u_statistic" in result
        assert "p_value" in result
        assert result["sample_sizes"]["ai"] == 1
        assert result["sample_sizes"]["non_ai"] == 1

    def test_unequal_sample_sizes(self):
        """Test with significantly different sample sizes."""
        ai_group = [2.0, 3.0, 4.0]  # n=3
        non_ai_group = [10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0]  # n=8

        result = run_mann_whitney_u(ai_group, non_ai_group)

        assert result["sample_sizes"]["ai"] == 3
        assert result["sample_sizes"]["non_ai"] == 8

        # Verify against scipy
        scipy_result = mannwhitneyu(ai_group, non_ai_group, alternative="two-sided")
        assert np.isclose(result["u_statistic"], scipy_result.statistic, rtol=1e-5)

    def test_effect_size_calculation(self):
        """Test that effect size r is calculated correctly."""
        ai_group = [1.0, 2.0, 3.0, 4.0, 5.0]
        non_ai_group = [10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0]

        result = run_mann_whitney_u(ai_group, non_ai_group)

        # Effect size r = Z / sqrt(N)
        # For Mann-Whitney U, we can verify it's in valid range
        assert 0 <= result["effect_size"] <= 1

        # Manual calculation check
        n1, n2 = len(ai_group), len(non_ai_group)
        n_total = n1 + n2
        u_stat = result["u_statistic"]

        # Calculate Z-score approximation for large samples
        # mu_U = n1 * n2 / 2
        # sigma_U = sqrt(n1 * n2 * (n1 + n2 + 1) / 12)
        mu_u = (n1 * n2) / 2
        sigma_u = np.sqrt((n1 * n2 * (n1 + n2 + 1)) / 12)
        z = (u_stat - mu_u) / sigma_u
        expected_r = abs(z) / np.sqrt(n_total)

        # Allow small tolerance due to scipy's exact vs asymptotic methods
        assert np.isclose(result["effect_size"], expected_r, rtol=0.1)

    def test_empty_ai_group(self):
        """Test handling of empty AI group."""
        ai_group = []
        non_ai_group = [5.0, 6.0, 7.0]

        with pytest.raises(ValueError, match="AI group cannot be empty"):
            run_mann_whitney_u(ai_group, non_ai_group)

    def test_empty_non_ai_group(self):
        """Test handling of empty non-AI group."""
        ai_group = [5.0, 6.0, 7.0]
        non_ai_group = []

        with pytest.raises(ValueError, match="Non-AI group cannot be empty"):
            run_mann_whitney_u(ai_group, non_ai_group)

    def test_stratified_consistency(self):
        """Test that MWU results are consistent across stratified subsets."""
        # Create data where AI group should consistently have lower values
        ai_group = np.random.RandomState(42).normal(3.0, 1.0, 50)
        non_ai_group = np.random.RandomState(43).normal(10.0, 2.0, 100)

        result = run_mann_whitney_u(ai_group, non_ai_group)

        # Should find significant difference (p < 0.05)
        assert result["p_value"] < 0.05

        # Effect size should be moderate to large
        assert result["effect_size"] > 0.3


class TestCalculateEffectSizeR:
    """Tests for the effect size calculation function."""

    def test_effect_size_formula(self):
        """Test that effect size r follows the correct formula."""
        u_stat = 100.0
        n1, n2 = 20, 30
        n_total = n1 + n2

        # Expected r = |Z| / sqrt(N)
        mu_u = (n1 * n2) / 2
        sigma_u = np.sqrt((n1 * n2 * (n1 + n2 + 1)) / 12)
        z = abs(u_stat - mu_u) / sigma_u
        expected_r = z / np.sqrt(n_total)

        calculated_r = calculate_effect_size_r(u_stat, n1, n2)

        assert np.isclose(calculated_r, expected_r, rtol=1e-5)

    def test_effect_size_bounds(self):
        """Test that effect size is always between 0 and 1."""
        # Test with various U statistics
        test_cases = [
            (0, 10, 10),
            (50, 10, 10),
            (100, 10, 10),
            (0, 5, 20),
            (100, 50, 50),
        ]

        for u_stat, n1, n2 in test_cases:
            r = calculate_effect_size_r(u_stat, n1, n2)
            assert 0 <= r <= 1, f"Effect size {r} out of bounds for U={u_stat}, n1={n1}, n2={n2}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])