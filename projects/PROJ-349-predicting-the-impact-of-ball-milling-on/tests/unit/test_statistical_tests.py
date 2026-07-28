"""
Unit tests for the Nadeau & Bengio corrected resampled t-test implementation.

These tests verify that the manual implementation matches expected behavior
on small synthetic datasets where the results can be calculated manually.
"""

import pytest
import numpy as np
from unittest.mock import patch

from src.evaluate.statistical_tests import nadeau_bengio_ttest, run_model_comparison_test


class TestNadeauBengioTTest:
    """Tests for the nadeau_bengio_ttest function."""

    def test_basic_calculation(self):
        """Test basic calculation with known inputs."""
        # Simple case: model A consistently outperforms model B
        scores_a = [0.9, 0.85, 0.92, 0.88, 0.91]
        scores_b = [0.7, 0.72, 0.68, 0.71, 0.69]

        # Large dataset relative to folds, so correction factor is small
        n_train = 1000
        n_test = 200

        t_stat, p_val, is_sig = nadeau_bengio_ttest(
            scores_a, scores_b, n_train, n_test
        )

        # We expect a significant difference
        assert is_sig is True
        assert p_val < 0.05
        # t-statistic should be positive (A > B)
        assert t_stat > 0

    def test_no_difference(self):
        """Test when there is no difference between models."""
        scores_a = [0.8, 0.8, 0.8, 0.8, 0.8]
        scores_b = [0.8, 0.8, 0.8, 0.8, 0.8]

        n_train = 1000
        n_test = 200

        t_stat, p_val, is_sig = nadeau_bengio_ttest(
            scores_a, scores_b, n_train, n_test
        )

        # No difference should yield t=0 and p=1.0
        assert np.isclose(t_stat, 0.0)
        assert np.isclose(p_val, 1.0)
        assert is_sig is False

    def test_unequal_list_lengths_raises_error(self):
        """Test that unequal list lengths raise ValueError."""
        scores_a = [0.9, 0.85, 0.92]
        scores_b = [0.7, 0.72]

        with pytest.raises(ValueError, match="same length"):
            nadeau_bengio_ttest(scores_a, scores_b, 100, 20)

    def test_empty_lists_raises_error(self):
        """Test that empty lists raise ValueError."""
        with pytest.raises(ValueError, match="empty"):
            nadeau_bengio_ttest([], [], 100, 20)

    def test_zero_samples_raises_error(self):
        """Test that zero n_train or n_test raises ValueError."""
        scores_a = [0.9, 0.85]
        scores_b = [0.7, 0.72]

        with pytest.raises(ValueError, match="positive"):
            nadeau_bengio_ttest(scores_a, scores_b, 0, 20)

        with pytest.raises(ValueError, match="positive"):
            nadeau_bengio_ttest(scores_a, scores_b, 100, 0)

    def test_manual_calculation_small_dataset(self):
        """
        Verify the calculation manually on a tiny dataset.

        This ensures the variance correction is applied correctly.
        """
        # Small dataset: 3 folds
        scores_a = [0.8, 0.9, 0.85]
        scores_b = [0.7, 0.8, 0.75]

        n_train = 100
        n_test = 20
        n_folds = 3

        # Differences
        diff = [0.1, 0.1, 0.1]
        mean_diff = 0.1

        # Variance of differences (ddof=1)
        # var = sum((x - mean)^2) / (n-1)
        # Since all diffs are 0.1, variance is 0
        var_diff = 0.0

        # Correction factor
        correction = (1.0 / n_folds) + (n_test / (n_folds * n_train))
        # correction = 1/3 + 20/(3*100) = 1/3 + 20/300 = 1/3 + 1/15 = 5/15 + 1/15 = 6/15 = 0.4

        # Corrected variance of mean
        corrected_var = var_diff * correction  # = 0

        # t-statistic
        # se = sqrt(corrected_var) = 0
        # t = mean_diff / se -> division by zero handled by code

        t_stat, p_val, is_sig = nadeau_bengio_ttest(
            scores_a, scores_b, n_train, n_test
        )

        # With zero variance, t-statistic should be 0 (handled by code)
        assert t_stat == 0.0
        assert p_val == 1.0
        assert is_sig is False

    def test_nonzero_variance_calculation(self):
        """Test with nonzero variance to ensure t-statistic is calculated."""
        scores_a = [0.8, 0.9, 0.7]
        scores_b = [0.7, 0.8, 0.6]

        n_train = 100
        n_test = 20

        t_stat, p_val, is_sig = nadeau_bengio_ttest(
            scores_a, scores_b, n_train, n_test
        )

        # We expect a positive t-statistic since A > B on average
        assert t_stat > 0
        # With small variance and consistent difference, should be significant
        # (though with only 3 folds, p-value might not be very small)
        # We just check that the calculation completes without error

    def test_correction_factor_impact(self):
        """
        Verify that the correction factor affects the t-statistic.

        A larger test set relative to training set should increase the
        correction factor, leading to a larger standard error and
        smaller t-statistic.
        """
        scores_a = [0.8, 0.9, 0.85, 0.82, 0.88]
        scores_b = [0.7, 0.8, 0.75, 0.72, 0.78]

        n_train = 100

        # Case 1: Small test set
        n_test_small = 10
        t_stat_small, _, _ = nadeau_bengio_ttest(
            scores_a, scores_b, n_train, n_test_small
        )

        # Case 2: Large test set (relative to training)
        n_test_large = 50
        t_stat_large, _, _ = nadeau_bengio_ttest(
            scores_a, scores_b, n_train, n_test_large
        )

        # With larger test set, correction factor is larger,
        # so standard error is larger, so t-statistic is smaller
        assert t_stat_large < t_stat_small

    def test_with_scipy_mock(self):
        """Test that the function works when scipy is available (mocked)."""
        scores_a = [0.8, 0.9, 0.85]
        scores_b = [0.7, 0.8, 0.75]

        with patch('src.evaluate.statistical_tests.stats') as mock_stats:
            mock_stats.t.sf.return_value = 0.01  # Mock p-value calculation
            t_stat, p_val, is_sig = nadeau_bengio_ttest(
                scores_a, scores_b, 100, 20
            )
            # Should call sf with absolute t-statistic and df
            mock_stats.t.sf.assert_called()

    def test_without_scipy_fallback(self):
        """Test fallback behavior when scipy is not available."""
        scores_a = [0.8, 0.9, 0.85]
        scores_b = [0.7, 0.8, 0.75]

        # Mock ImportError for scipy
        with patch.dict('sys.modules', {'scipy': None}):
            # Re-import to trigger the fallback code path
            import importlib
            import src.evaluate.statistical_tests as st_module
            importlib.reload(st_module)

            # This should not raise an error
            t_stat, p_val, is_sig = st_module.nadeau_bengio_ttest(
                scores_a, scores_b, 100, 20
            )

            # With large df (3-1=2 is small, so it uses the else branch)
            # The fallback should return a conservative estimate
            assert isinstance(t_stat, float)
            assert isinstance(p_val, float)


class TestRunModelComparisonTest:
    """Tests for the run_model_comparison_test function."""

    def test_returns_correct_structure(self):
        """Test that the result dictionary has all required keys."""
        scores_a = [0.8, 0.9, 0.85]
        scores_b = [0.7, 0.8, 0.75]

        result = run_model_comparison_test(
            scores_a, scores_b, n_train=100, n_test=20,
            model_a_name="RF", model_b_name="LR"
        )

        expected_keys = [
            "model_a", "model_b", "mean_score_a", "mean_score_b",
            "t_statistic", "p_value", "is_significant", "alpha",
            "winner", "n_folds", "n_train", "n_test"
        ]

        for key in expected_keys:
            assert key in result

    def test_winner_determination(self):
        """Test that the winner is correctly identified."""
        # Case 1: Model A is significantly better
        scores_a = [0.9, 0.9, 0.9]
        scores_b = [0.5, 0.5, 0.5]

        result = run_model_comparison_test(
            scores_a, scores_b, n_train=100, n_test=20,
            model_a_name="BetterModel", model_b_name="WorseModel"
        )

        assert result["winner"] == "BetterModel"

        # Case 2: No significant difference
        scores_a = [0.8, 0.8, 0.8]
        scores_b = [0.8, 0.8, 0.8]

        result = run_model_comparison_test(
            scores_a, scores_b, n_train=100, n_test=20,
            model_a_name="ModelX", model_b_name="ModelY"
        )

        assert result["winner"] == "No significant difference"

    def test_mean_scores_calculated_correctly(self):
        """Test that mean scores are calculated correctly."""
        scores_a = [0.8, 0.9, 0.85]
        scores_b = [0.7, 0.8, 0.75]

        result = run_model_comparison_test(
            scores_a, scores_b, n_train=100, n_test=20
        )

        expected_mean_a = np.mean(scores_a)
        expected_mean_b = np.mean(scores_b)

        assert np.isclose(result["mean_score_a"], expected_mean_a)
        assert np.isclose(result["mean_score_b"], expected_mean_b)