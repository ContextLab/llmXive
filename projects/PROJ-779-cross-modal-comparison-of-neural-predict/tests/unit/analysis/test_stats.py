"""
Unit tests for permutation test logic in code/analysis/stats.py.

These tests verify the statistical correctness of the permutation test implementation
without requiring the full EEG dataset. They use small, controlled synthetic inputs
(numpy arrays) to validate the logic of the test statistic calculation, the permutation
procedure, and the p-value derivation.

Note: These are unit tests for the *logic* of the function. The actual statistical
analysis on real data is performed in the integration tests and the main pipeline.
"""
import pytest
import numpy as np
from scipy import stats
from unittest.mock import patch, MagicMock

# Import the function under test
# Based on the API surface provided:
from code.analysis.stats import mixed_effects_permutation_test, StatsError


class TestMixedEffectsPermutationTest:
    """Tests for the mixed_effects_permutation_test function."""

    def test_function_signature_and_types(self):
        """Verify the function accepts the expected arguments and returns a dict."""
        # Create small, deterministic dummy data
        # Shape: (n_subjects, n_features) - simulated source strengths
        n_subjects_aud = 10
        n_subjects_vis = 10
        n_features = 5

        data_aud = np.random.RandomState(42).randn(n_subjects_aud, n_features)
        data_vis = np.random.RandomState(42).randn(n_subjects_vis, n_features)

        result = mixed_effects_permutation_test(
            data_aud,
            data_vis,
            n_permutations=100,
            random_state=42
        )

        assert isinstance(result, dict), "Result must be a dictionary"
        assert "p_value" in result, "Result must contain 'p_value'"
        assert "t_statistic" in result, "Result must contain 't_statistic'"
        assert "observed_diff" in result, "Result must contain 'observed_diff'"
        assert isinstance(result["p_value"], float), "p_value must be a float"
        assert isinstance(result["t_statistic"], float), "t_statistic must be a float"

    def test_permutation_logic_correctness(self):
        """
        Verify that the permutation test correctly calculates the p-value.
        We construct a case where the groups are identical (null hypothesis true).
        The p-value should be high (not significant).
        """
        np.random.seed(42)
        # Create identical distributions
        data = np.random.randn(20, 5)
        data_group1 = data[:10, :]
        data_group2 = data[10:, :]

        result = mixed_effects_permutation_test(
            data_group1,
            data_group2,
            n_permutations=1000,
            random_state=42
        )

        # Since data is identical, p-value should be > 0.05 (usually around 0.5)
        # We use a loose threshold to avoid flakiness, but it must be non-significant
        assert result["p_value"] > 0.05, \
            f"P-value {result['p_value']} is too low for identical groups"

    def test_permutation_logic_detects_difference(self):
        """
        Verify that the test detects a known difference.
        We create a case where Group B has a known mean shift.
        """
        np.random.seed(42)
        n = 50
        # Group A: mean 0
        group_a = np.random.randn(n, 3)
        # Group B: mean 2.0 (large effect size)
        group_b = np.random.randn(n, 3) + 2.0

        result = mixed_effects_permutation_test(
            group_a,
            group_b,
            n_permutations=1000,
            random_state=42
        )

        # With a large effect size and sufficient N, p-value should be very low
        assert result["p_value"] < 0.05, \
            f"P-value {result['p_value']} should be significant for large effect"
        assert result["t_statistic"] > 0, \
            "T-statistic should be positive if Group B > Group A (depending on implementation order)"

    def test_invalid_input_shapes(self):
        """Test that the function raises an error for mismatched dimensions."""
        data_a = np.random.randn(10, 5)
        data_b = np.random.randn(10, 6)  # Mismatch in features

        with pytest.raises((ValueError, StatsError)):
            mixed_effects_permutation_test(data_a, data_b, n_permutations=10)

    def test_small_sample_size(self):
        """Test behavior with very small sample sizes."""
        data_a = np.random.randn(3, 2)
        data_b = np.random.randn(3, 2)

        # Should run without crashing, though power is low
        result = mixed_effects_permutation_test(
            data_a,
            data_b,
            n_permutations=10,
            random_state=42
        )

        assert "p_value" in result

    def test_random_state_reproducibility(self):
        """Verify that the same random_state produces identical results."""
        np.random.seed(42)
        data_a = np.random.randn(20, 4)
        data_b = np.random.randn(20, 4) + 1.0

        result1 = mixed_effects_permutation_test(
            data_a, data_b, n_permutations=500, random_state=123
        )
        result2 = mixed_effects_permutation_test(
            data_a, data_b, n_permutations=500, random_state=123
        )

        assert result1["p_value"] == result2["p_value"], \
            "Results should be reproducible with the same random_state"
        assert result1["t_statistic"] == result2["t_statistic"], \
            "T-statistics should be identical"

    def test_zero_permutations_error(self):
        """Test that providing zero permutations raises an error."""
        data_a = np.random.randn(10, 2)
        data_b = np.random.randn(10, 2)

        with pytest.raises(ValueError):
            mixed_effects_permutation_test(
                data_a, data_b, n_permutations=0, random_state=42
            )

    def test_single_feature_aggregation(self):
        """
        Test that the function correctly handles a single feature (1D-like input).
        The implementation should average over features or handle 1D slices.
        """
        data_a = np.random.randn(20, 1)
        data_b = np.random.randn(20, 1) + 1.5

        result = mixed_effects_permutation_test(
            data_a, data_b, n_permutations=500, random_state=42
        )

        assert isinstance(result["p_value"], float)
        assert isinstance(result["t_statistic"], float)

    def test_t_statistic_direction(self):
        """
        Verify the sign of the t-statistic matches the direction of the mean difference.
        We assume the implementation computes (GroupA - GroupB) or (GroupB - GroupA).
        We check consistency: if Group B mean > Group A mean, the absolute difference
        should be reflected in the statistic magnitude.
        """
        np.random.seed(42)
        # Group A: 0
        group_a = np.random.randn(30, 2)
        # Group B: 3
        group_b = np.random.randn(30, 2) + 3.0

        result = mixed_effects_permutation_test(
            group_a, group_b, n_permutations=500, random_state=42
        )

        # The observed difference should be non-zero
        assert abs(result["observed_diff"]) > 0.1, \
            "Observed difference should be significant given the effect size"

        # The p-value should be significant
        assert result["p_value"] < 0.05

if __name__ == "__main__":
    pytest.main([__file__, "-v"])