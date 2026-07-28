import pytest
import numpy as np
from src.evaluate.statistical_tests import nadeau_bengio_ttest, compare_models


class TestNadeauBengioTTest:
    """Test the Nadeau & Bengio corrected resampled t-test implementation."""

    def test_identical_scores(self):
        """When scores are identical, t-statistic should be 0 and p-value 1."""
        scores = [0.8, 0.85, 0.9, 0.82, 0.88]
        t_stat, p_value, is_significant = nadeau_bengio_ttest(
            scores, scores, n_train=100, n_test=20
        )
        assert np.isclose(t_stat, 0.0, atol=1e-10)
        assert np.isclose(p_value, 1.0, atol=1e-10)
        assert not is_significant

    def test_clear_difference(self):
        """When one model is clearly better, test should be significant."""
        scores_a = [0.9, 0.92, 0.91, 0.93, 0.94]
        scores_b = [0.7, 0.72, 0.71, 0.73, 0.74]
        t_stat, p_value, is_significant = nadeau_bengio_ttest(
            scores_a, scores_b, n_train=100, n_test=20
        )
        assert t_stat > 0  # Model A is better
        assert p_value < 0.05
        assert is_significant

    def test_variance_correction_effect(self):
        """Test that the variance correction factor is applied correctly."""
        # Create scores with a known difference
        scores_a = [0.8, 0.81, 0.82, 0.83, 0.84]
        scores_b = [0.7, 0.71, 0.72, 0.73, 0.74]

        # With a small test set relative to training, the correction should be small
        t_stat_small_test, p_small_test, _ = nadeau_bengio_ttest(
            scores_a, scores_b, n_train=1000, n_test=10
        )

        # With a large test set relative to training, the correction should be larger
        # (reducing the t-statistic)
        t_stat_large_test, p_large_test, _ = nadeau_bengio_ttest(
            scores_a, scores_b, n_train=100, n_test=100
        )

        # The t-statistic should be smaller when the test set is larger
        # (due to the correction factor)
        assert t_stat_small_test > t_stat_large_test

    def test_mismatched_lengths(self):
        """Should raise ValueError if scores have different lengths."""
        with pytest.raises(ValueError):
            nadeau_bengio_ttest([0.8, 0.9], [0.7], n_train=100, n_test=20)

    def test_empty_scores(self):
        """Should raise ValueError if scores are empty."""
        with pytest.raises(ValueError):
            nadeau_bengio_ttest([], [], n_train=100, n_test=20)

    def test_zero_variance(self):
        """Test handling of zero variance in differences."""
        # All differences are the same
        scores_a = [0.8, 0.8, 0.8, 0.8, 0.8]
        scores_b = [0.7, 0.7, 0.7, 0.7, 0.7]
        t_stat, p_value, is_significant = nadeau_bengio_ttest(
            scores_a, scores_b, n_train=100, n_test=20
        )
        # If mean difference is non-zero and variance is zero, it should be significant
        assert t_stat != 0
        assert is_significant

    def test_manual_calculation_match(self):
        """
        Verify the implementation matches the manual calculation of the Nadeau-Bengio formula.
        This is the core verification for T047.
        """
        # Create a small synthetic dataset with known values
        scores_a = np.array([0.85, 0.87, 0.82, 0.88, 0.84])
        scores_b = np.array([0.75, 0.78, 0.73, 0.79, 0.76])

        n_folds = len(scores_a)
        n_train = 100
        n_test = 20

        # Manual calculation
        diffs = scores_a - scores_b
        mean_diff = np.mean(diffs)
        var_diff = np.var(diffs, ddof=1)

        # Nadeau-Bengio correction
        correction_factor = (1.0 / n_folds) + (n_test / n_train)
        se_mean_diff = np.sqrt(correction_factor * var_diff)

        t_stat_manual = mean_diff / se_mean_diff

        # Call the function
        t_stat_func, p_value, is_significant = nadeau_bengio_ttest(
            scores_a, scores_b, n_train, n_test
        )

        # Verify the t-statistic matches the manual calculation
        assert np.isclose(t_stat_func, t_stat_manual, rtol=1e-5), (
            f"t-statistic mismatch: function={t_stat_func}, manual={t_stat_manual}"
        )

    def test_alpha_threshold(self):
        """Test that significance is correctly determined by alpha."""
        scores_a = [0.8, 0.81, 0.82, 0.83, 0.84]
        scores_b = [0.7, 0.71, 0.72, 0.73, 0.74]

        # With alpha=0.05
        _, p_val_05, is_sig_05 = nadeau_bengio_ttest(
            scores_a, scores_b, n_train=100, n_test=20, alpha=0.05
        )

        # With alpha=0.01
        _, p_val_01, is_sig_01 = nadeau_bengio_ttest(
            scores_a, scores_b, n_train=100, n_test=20, alpha=0.01
        )

        # The p-value is the same, but significance depends on alpha
        # If p < 0.01, both should be significant
        # If 0.01 <= p < 0.05, only alpha=0.05 should be significant
        # If p >= 0.05, neither should be significant

        # We check the logic, not the specific p-value
        if p_val_05 < 0.05:
            assert is_sig_05
        else:
            assert not is_sig_05

        if p_val_01 < 0.01:
            assert is_sig_01
        else:
            assert not is_sig_01


class TestCompareModels:
    """Test the compare_models wrapper function."""

    def test_compare_models_structure(self):
        """Verify the output structure of compare_models."""
        scores_a = [0.8, 0.85, 0.9, 0.82, 0.88]
        scores_b = [0.7, 0.75, 0.8, 0.72, 0.78]

        result = compare_models(
            scores_a, scores_b, n_train=100, n_test=20,
            model_a_name="GPR", model_b_name="RF"
        )

        assert "t_statistic" in result
        assert "p_value" in result
        assert "is_significant" in result
        assert "alpha" in result
        assert "mean_a" in result
        assert "mean_b" in result
        assert "difference" in result
        assert "model_a_name" in result
        assert "model_b_name" in result
        assert "n_folds" in result
        assert "summary" in result

        assert result["model_a_name"] == "GPR"
        assert result["model_b_name"] == "RF"
        assert result["n_folds"] == 5
        assert result["n_train"] == 100
        assert result["n_test"] == 20

    def test_compare_models_significance(self):
        """Test that significance is correctly reported."""
        scores_a = [0.9, 0.92, 0.91, 0.93, 0.94]
        scores_b = [0.7, 0.72, 0.71, 0.73, 0.74]

        result = compare_models(scores_a, scores_b, n_train=100, n_test=20)

        assert result["is_significant"]
        assert "significant" in result["summary"].lower()

    def test_compare_models_not_significant(self):
        """Test that non-significance is correctly reported."""
        scores_a = [0.8, 0.81, 0.82, 0.83, 0.84]
        scores_b = [0.79, 0.80, 0.81, 0.82, 0.83]

        result = compare_models(scores_a, scores_b, n_train=100, n_test=20)

        assert not result["is_significant"]
        assert "not significant" in result["summary"].lower()