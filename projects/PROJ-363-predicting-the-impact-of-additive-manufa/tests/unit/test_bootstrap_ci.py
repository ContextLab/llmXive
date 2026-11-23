"""
Unit tests for Bootstrap Confidence Interval calculation logic.

This module verifies that the bootstrap resampling logic used to calculate
confidence intervals for SHAP values is implemented correctly.

Dependencies:
- code/analyze_explainability.py (specifically calculate_bootstrap_shap_ci)
- numpy, scipy
"""
import numpy as np
import pytest
from pathlib import Path
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from analyze_explainability import calculate_bootstrap_shap_ci


class TestBootstrapCI:
    """Test suite for bootstrap confidence interval calculations."""

    def test_basic_ci_calculation(self):
        """Test that basic CI calculation returns expected structure."""
        # Create synthetic SHAP values for a single feature
        np.random.seed(42)
        shap_values = np.random.normal(loc=0.5, scale=0.2, size=1000)
        
        result = calculate_bootstrap_shap_ci(shap_values, n_iterations=100, seed=42)
        
        # Check result structure
        assert isinstance(result, dict), "Result must be a dictionary"
        assert "mean" in result, "Result must contain 'mean'"
        assert "ci_lower" in result, "Result must contain 'ci_lower'"
        assert "ci_upper" in result, "Result must contain 'ci_upper'"
        assert "ci_level" in result, "Result must contain 'ci_level'"
        
        # Check types
        assert isinstance(result["mean"], float), "Mean must be a float"
        assert isinstance(result["ci_lower"], float), "CI lower must be a float"
        assert isinstance(result["ci_upper"], float), "CI upper must be a float"
        assert isinstance(result["ci_level"], float), "CI level must be a float"

    def test_ci_bounds_order(self):
        """Test that CI lower bound is always less than or equal to upper bound."""
        np.random.seed(42)
        shap_values = np.random.normal(loc=0.0, scale=1.0, size=500)
        
        result = calculate_bootstrap_shap_ci(shap_values, n_iterations=100, seed=42)
        
        assert result["ci_lower"] <= result["ci_upper"], \
            f"CI lower ({result['ci_lower']}) must be <= CI upper ({result['ci_upper']})"

    def test_ci_coverage_with_known_distribution(self):
        """
        Test that CI calculation works correctly with a known distribution.
        For a normal distribution, the mean should be within the 95% CI.
        """
        np.random.seed(42)
        true_mean = 0.5
        true_std = 0.1
        shap_values = np.random.normal(loc=true_mean, scale=true_std, size=2000)
        
        result = calculate_bootstrap_shap_ci(shap_values, n_iterations=500, seed=42)
        
        # The calculated mean should be close to the true mean
        assert abs(result["mean"] - true_mean) < 0.05, \
            f"Calculated mean {result['mean']} should be close to true mean {true_mean}"
        
        # The true mean should be within the 95% CI (with high probability)
        assert result["ci_lower"] <= true_mean <= result["ci_upper"], \
            f"True mean {true_mean} should be within CI [{result['ci_lower']}, {result['ci_upper']}]"

    def test_confidence_level_parameter(self):
        """Test that different confidence levels produce different intervals."""
        np.random.seed(42)
        shap_values = np.random.normal(loc=0.5, scale=0.2, size=1000)
        
        result_95 = calculate_bootstrap_shap_ci(shap_values, n_iterations=200, ci_level=0.95, seed=42)
        result_90 = calculate_bootstrap_shap_ci(shap_values, n_iterations=200, ci_level=0.90, seed=42)
        result_99 = calculate_bootstrap_shap_ci(shap_values, n_iterations=200, ci_level=0.99, seed=42)
        
        # Higher confidence level should produce wider intervals
        width_95 = result_95["ci_upper"] - result_95["ci_lower"]
        width_90 = result_90["ci_upper"] - result_90["ci_lower"]
        width_99 = result_99["ci_upper"] - result_99["ci_lower"]
        
        assert width_90 <= width_95, \
            f"90% CI width ({width_90}) should be <= 95% CI width ({width_95})"
        assert width_95 <= width_99, \
            f"95% CI width ({width_95}) should be <= 99% CI width ({width_99})"

    def test_reproducibility_with_seed(self):
        """Test that results are reproducible with the same seed."""
        np.random.seed(42)
        shap_values = np.random.normal(loc=0.5, scale=0.2, size=1000)
        
        result_1 = calculate_bootstrap_shap_ci(shap_values, n_iterations=200, seed=123)
        result_2 = calculate_bootstrap_shap_ci(shap_values, n_iterations=200, seed=123)
        
        assert result_1["mean"] == result_2["mean"], "Mean should be identical with same seed"
        assert result_1["ci_lower"] == result_2["ci_lower"], "CI lower should be identical with same seed"
        assert result_1["ci_upper"] == result_2["ci_upper"], "CI upper should be identical with same seed"

    def test_zero_variance_input(self):
        """Test behavior with zero variance input (all values identical)."""
        shap_values = np.ones(100) * 0.5  # All values are 0.5
        
        result = calculate_bootstrap_shap_ci(shap_values, n_iterations=100, seed=42)
        
        # Mean should be exactly 0.5
        assert result["mean"] == 0.5, "Mean should be 0.5 for constant input"
        # CI bounds should also be 0.5 (no variance)
        assert result["ci_lower"] == 0.5, "CI lower should be 0.5 for constant input"
        assert result["ci_upper"] == 0.5, "CI upper should be 0.5 for constant input"

    def test_large_sample_size(self):
        """Test with a large sample size to ensure stability."""
        np.random.seed(42)
        shap_values = np.random.normal(loc=0.3, scale=0.15, size=5000)
        
        result = calculate_bootstrap_shap_ci(shap_values, n_iterations=500, seed=42)
        
        # Mean should be close to 0.3
        assert abs(result["mean"] - 0.3) < 0.02, \
            f"Mean {result['mean']} should be close to 0.3 for large sample"

    def test_invalid_ci_level(self):
        """Test that invalid confidence levels raise appropriate errors."""
        np.random.seed(42)
        shap_values = np.random.normal(loc=0.5, scale=0.2, size=100)
        
        # Test ci_level > 1
        with pytest.raises(ValueError):
            calculate_bootstrap_shap_ci(shap_values, n_iterations=100, ci_level=1.5, seed=42)
        
        # Test ci_level <= 0
        with pytest.raises(ValueError):
            calculate_bootstrap_shap_ci(shap_values, n_iterations=100, ci_level=0.0, seed=42)
        
        # Test ci_level < 0
        with pytest.raises(ValueError):
            calculate_bootstrap_shap_ci(shap_values, n_iterations=100, ci_level=-0.5, seed=42)

    def test_single_feature_array(self):
        """Test with a 1D array (single feature)."""
        np.random.seed(42)
        shap_values = np.random.normal(loc=0.5, scale=0.2, size=500)
        
        result = calculate_bootstrap_shap_ci(shap_values, n_iterations=100, seed=42)
        
        # Should return a scalar-like result for single feature
        assert isinstance(result["mean"], float), "Mean should be a float for 1D input"
        assert isinstance(result["ci_lower"], float), "CI lower should be a float for 1D input"
        assert isinstance(result["ci_upper"], float), "CI upper should be a float for 1D input"

    def test_n_iterations_parameter(self):
        """Test that the number of iterations is respected."""
        np.random.seed(42)
        shap_values = np.random.normal(loc=0.5, scale=0.2, size=500)
        
        # Small number of iterations
        result_small = calculate_bootstrap_shap_ci(shap_values, n_iterations=10, seed=42)
        
        # Large number of iterations
        result_large = calculate_bootstrap_shap_ci(shap_values, n_iterations=1000, seed=42)
        
        # Both should return valid results, though with different precision
        assert result_small["mean"] is not None
        assert result_large["mean"] is not None
        
        # Larger sample should generally be more stable (though not guaranteed for small samples)
        # This is more of a sanity check than a strict assertion
        assert isinstance(result_small["mean"], float)
        assert isinstance(result_large["mean"], float)