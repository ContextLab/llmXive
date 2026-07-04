"""
Unit tests for meta-analysis module (Diebold-Mariano tests with Westfall-Young correction).
"""

import os
import sys
import tempfile
from pathlib import Path
import pandas as pd
import numpy as np
import pytest

from src.evaluation.meta_analysis import (
    diebold_mariano_test,
    westfall_young_stepdown_max_t,
    run_pairwise_dm_tests
)

class TestDieboldMariano:
    """Tests for the Diebold-Mariano test function."""

    def test_identical_forecasts(self):
        """DM test should return p-value near 1.0 for identical forecasts."""
        actual = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0])
        forecast = np.array([1.1, 2.1, 3.1, 4.1, 5.1, 6.1, 7.1, 8.1, 9.1, 10.1])

        dm_stat, p_value = diebold_mariano_test(actual, forecast, forecast)

        # For identical forecasts, loss difference should be ~0
        assert p_value > 0.5, "Identical forecasts should have high p-value"

    def test_different_forecast_accuracy(self):
        """DM test should detect significant difference when one forecast is clearly better."""
        actual = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0])
        forecast_a = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0])  # Perfect
        forecast_b = np.array([5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0, 13.0, 14.0])  # Bad

        dm_stat, p_value = diebold_mariano_test(actual, forecast_a, forecast_b)

        # Should detect significant difference
        assert p_value < 0.05, "Should detect significant difference between good and bad forecasts"

    def test_mismatched_lengths(self):
        """Should raise ValueError for mismatched lengths."""
        actual = np.array([1.0, 2.0, 3.0])
        forecast_a = np.array([1.0, 2.0])
        forecast_b = np.array([1.0, 2.0, 3.0])

        with pytest.raises(ValueError):
            diebold_mariano_test(actual, forecast_a, forecast_b)

    def test_absolute_loss_function(self):
        """Test with absolute loss function."""
        actual = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0])
        forecast_a = np.array([1.1, 2.1, 3.1, 4.1, 5.1, 6.1, 7.1, 8.1, 9.1, 10.1])
        forecast_b = np.array([1.2, 2.2, 3.2, 4.2, 5.2, 6.2, 7.2, 8.2, 9.2, 10.2])

        dm_stat, p_value = diebold_mariano_test(
            actual, forecast_a, forecast_b, loss_function="absolute"
        )

        assert isinstance(dm_stat, float)
        assert 0 <= p_value <= 1

    def test_unknown_loss_function(self):
        """Should raise ValueError for unknown loss function."""
        actual = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0])
        forecast_a = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0])
        forecast_b = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0])

        with pytest.raises(ValueError):
            diebold_mariano_test(actual, forecast_a, forecast_b, loss_function="unknown")

class TestWestfallYoung:
    """Tests for Westfall-Young step-down max-t correction."""

    def test_single_hypothesis(self):
        """Should handle single hypothesis test correctly."""
        np.random.seed(42)
        loss_diff = np.random.randn(100)
        loss_diffs = [loss_diff]

        adj_p_values, rejections = westfall_young_stepdown_max_t(
            loss_diffs, n_permutations=100, seed=42
        )

        assert len(adj_p_values) == 1
        assert len(rejections) == 1
        assert 0 <= adj_p_values[0] <= 1

    def test_multiple_hypotheses(self):
        """Should handle multiple hypothesis tests."""
        np.random.seed(42)
        loss_diffs = [np.random.randn(100) for _ in range(5)]

        adj_p_values, rejections = westfall_young_stepdown_max_t(
            loss_diffs, n_permutations=100, seed=42
        )

        assert len(adj_p_values) == 5
        assert len(rejections) == 5
        assert all(0 <= p <= 1 for p in adj_p_values)
        assert all(isinstance(r, bool) for r in rejections)

    def test_monotonicity(self):
        """Adjusted p-values should be monotonic (step-down property)."""
        np.random.seed(42)
        loss_diffs = [np.random.randn(100) for _ in range(10)]

        adj_p_values, _ = westfall_young_stepdown_max_t(
            loss_diffs, n_permutations=100, seed=42
        )

        # Check that p-values are non-decreasing when sorted by original statistic
        # (This is a property of step-down procedures)
        assert all(adj_p_values[i] <= adj_p_values[j] or i >= j
                  for i in range(len(adj_p_values))
                  for j in range(i+1, len(adj_p_values)))

    def test_alpha_threshold(self):
        """Rejections should depend on alpha threshold."""
        np.random.seed(42)
        # Create a strong signal
        loss_diffs = [np.random.randn(100) + 3.0 for _ in range(3)]

        _, rejections_alpha_05 = westfall_young_stepdown_max_t(
            loss_diffs, n_permutations=100, alpha=0.05, seed=42
        )

        _, rejections_alpha_01 = westfall_young_stepdown_max_t(
            loss_diffs, n_permutations=100, alpha=0.01, seed=42
        )

        # Should have fewer rejections at stricter alpha
        assert sum(rejections_alpha_01) <= sum(rejections_alpha_05)

class TestPairwiseDMTests:
    """Tests for pairwise DM test execution."""

    def test_empty_model_list(self):
        """Should handle empty model list gracefully."""
        forecasts_df = pd.DataFrame({"date": [1, 2, 3]})
        actual_outcomes = pd.Series([1.0, 2.0, 3.0])

        results = run_pairwise_dm_tests(forecasts_df, actual_outcomes, [])

        assert results["dm_stats"] == {}
        assert results["p_values"] == {}

    def test_single_model(self):
        """Should handle single model (no pairs to compare)."""
        forecasts_df = pd.DataFrame({
            "date": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            "model_a": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
        })
        actual_outcomes = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0])

        results = run_pairwise_dm_tests(
            forecasts_df, actual_outcomes, ["model_a"]
        )

        assert results["dm_stats"] == {}
        assert results["p_values"] == {}

    def test_two_models(self):
        """Should correctly compare two models."""
        np.random.seed(42)
        n = 50
        actual = np.random.randn(n)
        forecast_a = actual + np.random.randn(n) * 0.5
        forecast_b = actual + np.random.randn(n) * 1.0

        forecasts_df = pd.DataFrame({
            "date": range(n),
            "model_a": forecast_a,
            "model_b": forecast_b
        })
        actual_outcomes = pd.Series(actual)

        results = run_pairwise_dm_tests(
            forecasts_df, actual_outcomes, ["model_a", "model_b"],
            n_permutations=50, alpha=0.05
        )

        assert ("model_a", "model_b") in results["dm_stats"]
        assert ("model_a", "model_b") in results["p_values"]
        assert ("model_a", "model_b") in results["adjusted_p_values"]
        assert ("model_a", "model_b") in results["rejections"]
        assert results["comparison_matrix"] is not None

    def test_three_models(self):
        """Should handle three models with all pairwise comparisons."""
        np.random.seed(42)
        n = 50
        actual = np.random.randn(n)
        forecast_a = actual + np.random.randn(n) * 0.5
        forecast_b = actual + np.random.randn(n) * 0.7
        forecast_c = actual + np.random.randn(n) * 1.0

        forecasts_df = pd.DataFrame({
            "date": range(n),
            "model_a": forecast_a,
            "model_b": forecast_b,
            "model_c": forecast_c
        })
        actual_outcomes = pd.Series(actual)

        results = run_pairwise_dm_tests(
            forecasts_df, actual_outcomes, ["model_a", "model_b", "model_c"],
            n_permutations=50, alpha=0.05
        )

        # Should have 3 pairwise comparisons: (a,b), (a,c), (b,c)
        assert len(results["dm_stats"]) == 3
        assert len(results["p_values"]) == 3
        assert results["comparison_matrix"].shape == (3, 3)

    def test_mismatched_lengths_handling(self):
        """Should handle cases where forecasts and actuals have different lengths."""
        np.random.seed(42)
        forecasts_df = pd.DataFrame({
            "date": range(50),
            "model_a": np.random.randn(50),
            "model_b": np.random.randn(50)
        })
        actual_outcomes = pd.Series(np.random.randn(40))  # Shorter

        results = run_pairwise_dm_tests(
            forecasts_df, actual_outcomes, ["model_a", "model_b"],
            n_permutations=50, alpha=0.05
        )

        # Should still run, truncating to shortest length
        assert len(results["dm_stats"]) == 1

if __name__ == "__main__":
    pytest.main([__file__, "-v"])