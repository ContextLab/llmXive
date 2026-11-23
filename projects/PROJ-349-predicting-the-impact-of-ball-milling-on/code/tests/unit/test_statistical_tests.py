"""
Unit tests for statistical tests implementation.
Specifically tests the Nadeau & Bengio corrected t-test.
"""
import numpy as np
import pytest
import os
import sys
from pathlib import Path

# Add parent to path for imports if needed, though standard project structure handles this
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.evaluate.statistical_tests import nadeau_bengio_ttest, run_model_comparison_test


class TestNadeauBengioTTest:
    """Tests for the Nadeau & Bengio corrected t-test implementation."""

    def test_basic_calculation(self):
        """Test basic calculation with known values."""
        # Simulate scores where Model 1 is consistently better
        model1 = np.array([0.85, 0.86, 0.84, 0.87, 0.85])
        model2 = np.array([0.75, 0.76, 0.74, 0.77, 0.75])

        n_train = 400
        n_test = 100
        k = 5

        t_stat, p_value, is_significant = nadeau_bengio_ttest(
            model1, model2, n_train, n_test
        )

        # Since Model 1 is clearly better, t should be positive and large
        assert t_stat > 0
        # P-value should be very small (highly significant)
        assert p_value < 0.05
        assert is_significant

    def test_no_difference(self):
        """Test when there is no difference between models."""
        scores = np.array([0.80, 0.81, 0.79, 0.82, 0.80])

        t_stat, p_value, is_significant = nadeau_bengio_ttest(
            scores, scores, n_train=400, n_test=100
        )

        # T-stat should be 0 (or very close due to floating point)
        assert np.isclose(t_stat, 0.0)
        # P-value should be 1.0
        assert np.isclose(p_value, 1.0)
        assert not is_significant

    def test_variance_correction_factor(self):
        """
        Verify that the variance correction factor is applied correctly.
        We compare the standard error calculation manually.
        """
        model1 = np.array([0.8, 0.8, 0.8, 0.8, 0.8])
        model2 = np.array([0.7, 0.7, 0.7, 0.7, 0.7])

        n_train = 400
        n_test = 100
        k = 5
        n_total = n_train + n_test

        diffs = model1 - model2
        mean_diff = np.mean(diffs)
        var_diff = np.var(diffs, ddof=1)

        # Manual calculation of SE with Nadeau-Bengio correction
        correction_factor = (1.0 / k + float(n_test) / float(n_total))
        expected_se = np.sqrt(correction_factor * var_diff)

        # Get SE from function (by calculating t = mean / se => se = mean / t)
        # Handle case where t might be 0 or inf
        t_stat, _, _ = nadeau_bengio_ttest(model1, model2, n_train, n_test)

        if t_stat != 0:
            calculated_se = mean_diff / t_stat
            # Allow for some floating point tolerance
            assert np.isclose(calculated_se, expected_se, rtol=1e-5), \
                f"Expected SE {expected_se}, got {calculated_se}"

    def test_mismatched_lengths(self):
        """Test that mismatched lengths raise an error."""
        model1 = np.array([0.8, 0.8, 0.8])
        model2 = np.array([0.7, 0.7])

        with pytest.raises(ValueError):
            nadeau_bengio_ttest(model1, model2, n_train=40, n_test=10)

    def test_small_sample_size(self):
        """Test with a small number of folds (k=2)."""
        model1 = np.array([0.9, 0.85])
        model2 = np.array([0.8, 0.75])

        t_stat, p_value, is_significant = nadeau_bengio_ttest(
            model1, model2, n_train=50, n_test=50
        )

        # Should run without error
        assert isinstance(t_stat, float)
        assert isinstance(p_value, float)
        assert isinstance(is_significant, bool)

class TestRunModelComparisonTest:
    """Tests for the wrapper function run_model_comparison_test."""

    def test_return_structure(self):
        """Test that the return dictionary contains all expected keys."""
        model1 = [0.85, 0.86, 0.84]
        model2 = [0.75, 0.76, 0.74]

        result = run_model_comparison_test(
            model1, model2, n_train=100, n_test=50,
            model1_name="GPR", model2_name="RF"
        )

        expected_keys = [
            "model1_name", "model2_name", "model1_mean", "model2_mean",
            "mean_difference", "t_statistic", "p_value", "alpha",
            "is_significant", "folds", "n_train", "n_test"
        ]

        for key in expected_keys:
            assert key in result, f"Missing key: {key}"

        assert result["model1_name"] == "GPR"
        assert result["model2_name"] == "RF"
        assert result["folds"] == 3
        assert result["is_significant"] is True # Based on the large difference

    def test_alpha_threshold(self):
        """Test that alpha parameter affects significance."""
        model1 = [0.85, 0.86, 0.84]
        model2 = [0.84, 0.85, 0.83] # Very close

        result_low_alpha = run_model_comparison_test(
            model1, model2, n_train=100, n_test=50, alpha=0.01
        )
        result_high_alpha = run_model_comparison_test(
            model1, model2, n_train=100, n_test=50, alpha=0.10
        )

        # With very close scores, p-value might be high.
        # If p > 0.01, low_alpha result is False.
        # If p < 0.10, high_alpha result is True.
        # We just check that the logic holds:
        if result_low_alpha["p_value"] < 0.01:
            assert result_low_alpha["is_significant"] is True
        else:
            assert result_low_alpha["is_significant"] is False

        if result_high_alpha["p_value"] < 0.10:
            assert result_high_alpha["is_significant"] is True
        else:
            assert result_high_alpha["is_significant"] is False