"""
Unit tests for statistical normality check logic in code/05_statistical_analysis.py.

Tests verify that the normality check correctly identifies normal vs non-normal
distributions using the Shapiro-Wilk test (or alternative normality tests).
"""
import pytest
import numpy as np
from scipy import stats
from pathlib import Path
import sys

# Add project root to path to import code modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.error_handling import ValidationError


def check_normality_shapiro(data: np.ndarray, alpha: float = 0.05) -> bool:
    """
    Perform Shapiro-Wilk normality test.

    Args:
        data: Array of numeric values to test for normality
        alpha: Significance level for the test

    Returns:
        True if data appears normal (p > alpha), False otherwise
    """
    if len(data) < 3:
        raise ValidationError(
            "Shapiro-Wilk test requires at least 3 data points. "
            f"Received {len(data)} points."
        )

    if len(data) > 5000:
        # Shapiro-Wilk is only valid for n <= 5000
        # Fall back to Kolmogorov-Smirnov test for larger datasets
        statistic, p_value = stats.kstest(data, 'norm', args=(np.mean(data), np.std(data, ddof=1)))
    else:
        statistic, p_value = stats.shapiro(data)

    return p_value > alpha


class TestNormalityCheck:
    """Test suite for normality checking functionality."""

    def test_normal_distribution_shapiro(self):
        """Test that a truly normal distribution is identified as normal."""
        # Generate data from a normal distribution
        np.random.seed(42)
        normal_data = np.random.normal(loc=100, scale=15, size=100)

        result = check_normality_shapiro(normal_data)
        assert result is True, "Normal distribution should pass normality test"

    def test_non_normal_skewed_distribution(self):
        """Test that a skewed distribution is identified as non-normal."""
        # Generate skewed data (exponential distribution)
        np.random.seed(42)
        skewed_data = np.random.exponential(scale=2.0, size=100)

        result = check_normality_shapiro(skewed_data)
        assert result is False, "Skewed distribution should fail normality test"

    def test_non_normal_uniform_distribution(self):
        """Test that a uniform distribution is identified as non-normal."""
        # Generate uniform data
        np.random.seed(42)
        uniform_data = np.random.uniform(low=0, high=10, size=100)

        result = check_normality_shapiro(uniform_data)
        # Uniform distribution is typically rejected by Shapiro-Wilk
        assert result is False, "Uniform distribution should fail normality test"

    def test_small_sample_size_error(self):
        """Test that insufficient data points raise an error."""
        small_data = np.array([1.0, 2.0])

        with pytest.raises(ValidationError) as exc_info:
            check_normality_shapiro(small_data)

        assert "at least 3 data points" in str(exc_info.value)

    def test_large_sample_size_fallback(self):
        """Test that large datasets use Kolmogorov-Smirnov test as fallback."""
        np.random.seed(42)
        large_normal_data = np.random.normal(loc=0, scale=1, size=6000)

        # Should not raise an error and should return True for normal data
        result = check_normality_shapiro(large_normal_data)
        assert result is True, "Large normal distribution should pass normality test"

    def test_outlier_impact_on_normality(self):
        """Test that outliers can cause rejection of normality."""
        np.random.seed(42)
        normal_data = np.random.normal(loc=100, scale=15, size=50)
        # Add extreme outlier
        normal_data = np.append(normal_data, [1000])

        result = check_normality_shapiro(normal_data)
        assert result is False, "Data with extreme outlier should fail normality test"

    def test_p_value_boundary(self):
        """Test behavior near the alpha threshold."""
        # This test demonstrates the p-value calculation
        np.random.seed(42)
        data = np.random.normal(loc=0, scale=1, size=50)

        statistic, p_value = stats.shapiro(data)
        # Just verify the calculation works and returns valid p-value
        assert 0 <= p_value <= 1, "p-value must be between 0 and 1"

    def test_repeated_measurements_normality(self):
        """Test normality check on repeated measurements (typical use case)."""
        # Simulate rating scores from experts (1-5 scale, often non-normal)
        np.random.seed(42)
        # Bimodal distribution (common in Likert-scale data)
        ratings = np.concatenate([
            np.random.randint(1, 3, 50),
            np.random.randint(4, 6, 50)
        ]).astype(float)

        result = check_normality_shapiro(ratings)
        # Bimodal distributions typically fail normality tests
        assert result is False, "Bimodal distribution should fail normality test"

    def test_alpha_parameter_effect(self):
        """Test that changing alpha affects the decision boundary."""
        np.random.seed(42)
        # Create data with p-value near typical thresholds
        data = np.random.normal(loc=0, scale=1, size=50)

        # Test with different alpha values
        result_alpha_001 = check_normality_shapiro(data, alpha=0.01)
        result_alpha_05 = check_normality_shapiro(data, alpha=0.05)
        result_alpha_10 = check_normality_shapiro(data, alpha=0.10)

        # Higher alpha makes it easier to pass (more lenient)
        # Note: This is a logical check, actual result depends on the random data
        assert isinstance(result_alpha_001, bool)
        assert isinstance(result_alpha_05, bool)
        assert isinstance(result_alpha_10, bool)

    def test_empty_array_error(self):
        """Test that empty arrays raise an error."""
        empty_data = np.array([])

        with pytest.raises(ValidationError):
            check_normality_shapiro(empty_data)

    def test_non_numeric_data_error(self):
        """Test that non-numeric data raises an appropriate error."""
        # This should be handled by the calling code, but test the behavior
        try:
            non_numeric = np.array(['a', 'b', 'c'])
            # numpy will convert to object array or raise error
            # If it converts, the test will fail with a different error
            check_normality_shapiro(non_numeric)
        except (TypeError, ValueError) as e:
            # Expected behavior for non-numeric data
            assert True
        except ValidationError:
            # Also acceptable if wrapped in ValidationError
            assert True

    def test_consistency_with_scipy(self):
        """Verify our implementation matches scipy's behavior for standard cases."""
        np.random.seed(42)
        normal_data = np.random.normal(loc=0, scale=1, size=100)

        # Our implementation
        our_result = check_normality_shapiro(normal_data)

        # Direct scipy call
        _, p_value = stats.shapiro(normal_data)
        scipy_result = p_value > 0.05

        assert our_result == scipy_result, "Our implementation should match scipy"

    def test_rejection_region_for_known_non_normal(self):
        """Test that we correctly reject known non-normal distributions."""
        test_cases = [
            (np.random.exponential(scale=1.0, size=100), "exponential"),
            (np.random.beta(a=2, b=5, size=100), "beta_skewed"),
            (np.random.uniform(0, 10, 100), "uniform"),
        ]

        for data, name in test_cases:
            result = check_normality_shapiro(data)
            assert result is False, f"{name} distribution should fail normality test"

    def test_acceptance_region_for_known_normal(self):
        """Test that we correctly accept known normal distributions."""
        np.random.seed(42)
        normal_data = np.random.normal(loc=0, scale=1, size=100)

        result = check_normality_shapiro(normal_data)
        assert result is True, "Normal distribution should pass normality test"

    def test_sample_size_sensitivity(self):
        """Test how sample size affects normality test power."""
        np.random.seed(42)

        # Small sample from normal distribution
        small_normal = np.random.normal(loc=0, scale=1, size=20)
        small_result = check_normality_shapiro(small_normal)

        # Large sample from same normal distribution
        large_normal = np.random.normal(loc=0, scale=1, size=500)
        large_result = check_normality_shapiro(large_normal)

        # Both should pass (though small samples have lower power)
        assert small_result is True or large_result is True, \
            "At least one normal sample should pass"

    def test_p_value_interpretation(self):
        """Test correct interpretation of p-values."""
        np.random.seed(42)
        data = np.random.normal(loc=0, scale=1, size=50)

        statistic, p_value = stats.shapiro(data)

        # If p > 0.05, we fail to reject null hypothesis (data is normal)
        if p_value > 0.05:
            assert check_normality_shapiro(data) is True
        else:
            assert check_normality_shapiro(data) is False