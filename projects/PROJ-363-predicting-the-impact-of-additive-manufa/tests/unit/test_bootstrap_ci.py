import numpy as np
import pytest
import sys
import os

# Add the code directory to the path to allow imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from analyze_explainability import calculate_bootstrap_shap_ci


class TestBootstrapConfidenceInterval:
    """Unit tests for Bootstrap Confidence Interval calculation logic."""

    def test_bootstrap_ci_returns_expected_structure(self):
        """Verify that the function returns a dictionary with required keys."""
        # Create synthetic SHAP values for testing (real logic is tested via integration)
        # We use a small, fixed dataset to ensure reproducibility
        np.random.seed(42)
        shap_values = np.random.randn(100, 5)  # 100 samples, 5 features

        result = calculate_bootstrap_shap_ci(shap_values, n_iterations=100, confidence_level=0.95)

        assert isinstance(result, dict), "Result must be a dictionary"
        assert "mean" in result, "Result must contain 'mean' key"
        assert "lower_bound" in result, "Result must contain 'lower_bound' key"
        assert "upper_bound" in result, "Result must contain 'upper_bound' key"
        assert "ci_level" in result, "Result must contain 'ci_level' key"

        # Check shapes
        assert result["mean"].shape == (5,), "Mean shape mismatch"
        assert result["lower_bound"].shape == (5,), "Lower bound shape mismatch"
        assert result["upper_bound"].shape == (5,), "Upper bound shape mismatch"
        assert result["ci_level"] == 0.95, "CI level mismatch"

    def test_bootstrap_ci_bounds_ordering(self):
        """Verify that lower_bound <= mean <= upper_bound for all features."""
        np.random.seed(123)
        shap_values = np.random.randn(200, 3)

        result = calculate_bootstrap_shap_ci(shap_values, n_iterations=200, confidence_level=0.95)

        # Check that bounds are ordered correctly
        assert np.all(result["lower_bound"] <= result["mean"]), "Lower bound should be <= mean"
        assert np.all(result["mean"] <= result["upper_bound"]), "Mean should be <= upper bound"

    def test_bootstrap_ci_width_increases_with_variance(self):
        """Verify that higher variance in SHAP values leads to wider confidence intervals."""
        np.random.seed(456)
        low_var_shap = np.random.randn(100, 2) * 0.1
        high_var_shap = np.random.randn(100, 2) * 10.0

        low_var_result = calculate_bootstrap_shap_ci(low_var_shap, n_iterations=100, confidence_level=0.95)
        high_var_result = calculate_bootstrap_shap_ci(high_var_shap, n_iterations=100, confidence_level=0.95)

        low_var_width = np.mean(high_var_result["upper_bound"] - high_var_result["lower_bound"])
        high_var_width = np.mean(high_var_result["upper_bound"] - high_var_result["lower_bound"])

        # The high variance dataset should have wider intervals
        assert high_var_width > low_var_width, "Higher variance should produce wider confidence intervals"

    def test_bootstrap_ci_with_constant_input(self):
        """Verify behavior when SHAP values are constant (zero variance)."""
        shap_values = np.ones((50, 3))  # All values are 1.0

        result = calculate_bootstrap_shap_ci(shap_values, n_iterations=50, confidence_level=0.95)

        # For constant input, mean, lower, and upper should all be approximately 1.0
        assert np.allclose(result["mean"], 1.0, atol=1e-5), "Mean should be 1.0 for constant input"
        assert np.allclose(result["lower_bound"], 1.0, atol=1e-5), "Lower bound should be 1.0 for constant input"
        assert np.allclose(result["upper_bound"], 1.0, atol=1e-5), "Upper bound should be 1.0 for constant input"

    def test_bootstrap_ci_respects_confidence_level(self):
        """Verify that changing confidence level changes interval width."""
        np.random.seed(789)
        shap_values = np.random.randn(300, 2)

        ci_90 = calculate_bootstrap_shap_ci(shap_values, n_iterations=300, confidence_level=0.90)
        ci_99 = calculate_bootstrap_shap_ci(shap_values, n_iterations=300, confidence_level=0.99)

        width_90 = np.mean(ci_90["upper_bound"] - ci_90["lower_bound"])
        width_99 = np.mean(ci_99["upper_bound"] - ci_99["lower_bound"])

        # Higher confidence level should produce wider intervals
        assert width_99 > width_90, "99% CI should be wider than 90% CI"
        assert ci_90["ci_level"] == 0.90, "CI level should be 0.90"
        assert ci_99["ci_level"] == 0.99, "CI level should be 0.99"

    def test_bootstrap_ci_deterministic_with_seed(self):
        """Verify that running with the same seed produces identical results."""
        np.random.seed(101)
        shap_values = np.random.randn(150, 2)

        result_1 = calculate_bootstrap_shap_ci(shap_values, n_iterations=150, confidence_level=0.95)
        result_2 = calculate_bootstrap_shap_ci(shap_values, n_iterations=150, confidence_level=0.95)

        # Results should be identical because the underlying function uses a fixed seed internally
        # or the randomness is controlled by the input state
        assert np.allclose(result_1["mean"], result_2["mean"]), "Mean should be reproducible"
        assert np.allclose(result_1["lower_bound"], result_2["lower_bound"]), "Lower bound should be reproducible"
        assert np.allclose(result_1["upper_bound"], result_2["upper_bound"]), "Upper bound should be reproducible"

    def test_bootstrap_ci_handles_single_feature(self):
        """Verify correct handling when there is only one feature."""
        np.random.seed(202)
        shap_values = np.random.randn(100, 1)

        result = calculate_bootstrap_shap_ci(shap_values, n_iterations=100, confidence_level=0.95)

        assert result["mean"].shape == (1,), "Mean shape should be (1,)"
        assert result["lower_bound"].shape == (1,), "Lower bound shape should be (1,)"
        assert result["upper_bound"].shape == (1,), "Upper bound shape should be (1,)"

    def test_bootstrap_ci_large_iterations_convergence(self):
        """Verify that increasing iterations leads to more stable estimates."""
        np.random.seed(303)
        shap_values = np.random.randn(500, 2)

        result_100 = calculate_bootstrap_shap_ci(shap_values, n_iterations=100, confidence_level=0.95)
        result_1000 = calculate_bootstrap_shap_ci(shap_values, n_iterations=1000, confidence_level=0.95)

        # The estimates should be reasonably close, though not identical due to randomness
        # We check that the difference is not excessively large
        mean_diff = np.abs(result_100["mean"] - result_1000["mean"]).mean()
        # Allow some tolerance due to stochastic nature, but it should be small
        assert mean_diff < 0.5, "Mean estimates should converge with more iterations"