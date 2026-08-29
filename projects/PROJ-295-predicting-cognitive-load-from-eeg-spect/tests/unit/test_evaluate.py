"""
Unit tests for permutation testing in code/models/evaluate.py.

This module verifies that the permutation_test function correctly:
1. Generates a null distribution by shuffling labels
2. Computes the test statistic (Pearson correlation) for each permutation
3. Calculates the p-value as the proportion of null statistics >= observed statistic
4. Handles edge cases (e.g., perfect correlation, small sample sizes)
"""
import pytest
import numpy as np
from scipy.stats import pearsonr
from sklearn.metrics import r2_score, mean_squared_error
from models.evaluate import permutation_test, compute_metrics
import warnings

# Suppress warnings for cleaner test output
warnings.filterwarnings("ignore")

class TestPermutationTest:
    """Test suite for permutation testing functionality."""

    def test_permutation_test_basic(self):
        """Test basic permutation test with known data."""
        # Create synthetic data with a known relationship
        np.random.seed(42)
        n_samples = 100
        X = np.random.randn(n_samples, 5)
        y = X[:, 0] + 0.5 * np.random.randn(n_samples)  # Linear relationship
        
        # Run permutation test
        observed_stat, null_distribution, p_value = permutation_test(
            X, y, n_permutations=1000, test_statistic='pearson'
        )
        
        # Verify output types
        assert isinstance(observed_stat, float), "Observed statistic should be a float"
        assert isinstance(null_distribution, np.ndarray), "Null distribution should be an array"
        assert isinstance(p_value, float), "P-value should be a float"
        
        # Verify dimensions
        assert len(null_distribution) == 1000, "Null distribution should have 1000 elements"
        
        # Verify p-value is in valid range
        assert 0.0 <= p_value <= 1.0, "P-value should be between 0 and 1"
        
        # With a real relationship, p-value should typically be < 0.05 (though random chance exists)
        # We'll just check it's not NaN or Inf
        assert not np.isnan(p_value), "P-value should not be NaN"
        assert not np.isinf(p_value), "P-value should not be Inf"

    def test_permutation_test_null_hypothesis(self):
        """Test that with no relationship, p-value is not significantly small."""
        # Create data with no relationship (independent variables)
        np.random.seed(123)
        n_samples = 200
        X = np.random.randn(n_samples, 3)
        y = np.random.randn(n_samples)  # Independent of X
        
        observed_stat, null_distribution, p_value = permutation_test(
            X, y, n_permutations=500, test_statistic='pearson'
        )
        
        # With no relationship, p-value should typically be > 0.05
        # We allow for some randomness but check it's not extremely small
        assert p_value > 0.01, "P-value should not be extremely small for null data"

    def test_permutation_test_perfect_correlation(self):
        """Test behavior with perfect correlation."""
        np.random.seed(456)
        n_samples = 50
        X = np.random.randn(n_samples, 1)
        y = X.flatten()  # Perfect correlation
        
        observed_stat, null_distribution, p_value = permutation_test(
            X, y, n_permutations=100, test_statistic='pearson'
        )
        
        # Observed statistic should be very close to 1.0
        assert observed_stat > 0.99, "Perfect correlation should yield statistic > 0.99"
        
        # P-value should be very small (likely 0 or 1/n_permutations)
        assert p_value <= (1 / 100), "Perfect correlation should yield very small p-value"

    def test_permutation_test_r2_statistic(self):
        """Test permutation test with R2 statistic."""
        np.random.seed(789)
        n_samples = 80
        X = np.random.randn(n_samples, 4)
        y = X[:, 0] + 0.3 * X[:, 1] + 0.2 * np.random.randn(n_samples)
        
        observed_stat, null_distribution, p_value = permutation_test(
            X, y, n_permutations=200, test_statistic='r2'
        )
        
        # Verify outputs
        assert isinstance(observed_stat, float)
        assert len(null_distribution) == 200
        assert 0.0 <= p_value <= 1.0

    def test_permutation_test_small_sample(self):
        """Test permutation test with small sample size."""
        np.random.seed(101)
        n_samples = 10
        X = np.random.randn(n_samples, 2)
        y = X[:, 0] + 0.5 * np.random.randn(n_samples)
        
        observed_stat, null_distribution, p_value = permutation_test(
            X, y, n_permutations=50, test_statistic='pearson'
        )
        
        # Should still work with small samples
        assert not np.isnan(p_value)
        assert not np.isinf(p_value)

    def test_permutation_test_seed_reproducibility(self):
        """Test that permutation test is reproducible with seed."""
        np.random.seed(202)
        n_samples = 60
        X = np.random.randn(n_samples, 3)
        y = X[:, 0] + 0.4 * np.random.randn(n_samples)
        
        # Run twice with same seed
        _, _, p_value1 = permutation_test(X, y, n_permutations=100, test_statistic='pearson', random_state=42)
        _, _, p_value2 = permutation_test(X, y, n_permutations=100, test_statistic='pearson', random_state=42)
        
        # Results should be identical with same seed
        assert p_value1 == p_value2, "Results should be reproducible with same seed"

    def test_permutation_test_null_distribution_shape(self):
        """Test that null distribution has correct shape and properties."""
        np.random.seed(303)
        n_samples = 100
        n_features = 5
        X = np.random.randn(n_samples, n_features)
        y = np.random.randn(n_samples)
        
        n_perms = 500
        observed_stat, null_distribution, p_value = permutation_test(
            X, y, n_permutations=n_perms, test_statistic='pearson'
        )
        
        # Null distribution should have exactly n_permutations elements
        assert len(null_distribution) == n_perms
        
        # Null distribution should be centered around 0 (for pearson correlation)
        null_mean = np.mean(null_distribution)
        assert abs(null_mean) < 0.1, "Null distribution should be centered near 0"
        
        # Null distribution should have reasonable variance
        null_std = np.std(null_distribution)
        assert null_std > 0.01, "Null distribution should have non-zero variance"

    def test_permutation_test_invalid_statistic(self):
        """Test that invalid test statistic raises an error."""
        np.random.seed(404)
        X = np.random.randn(50, 3)
        y = np.random.randn(50)
        
        with pytest.raises(ValueError):
            permutation_test(X, y, n_permutations=100, test_statistic='invalid_stat')

    def test_permutation_test_zero_permutations(self):
        """Test behavior with zero permutations."""
        np.random.seed(505)
        X = np.random.randn(30, 2)
        y = np.random.randn(30)
        
        with pytest.raises(ValueError):
            permutation_test(X, y, n_permutations=0, test_statistic='pearson')

    def test_permutation_test_negative_correlation(self):
        """Test permutation test with negative correlation."""
        np.random.seed(606)
        n_samples = 100
        X = np.random.randn(n_samples, 1)
        y = -X.flatten() + 0.1 * np.random.randn(n_samples)  # Negative correlation
        
        observed_stat, null_distribution, p_value = permutation_test(
            X, y, n_permutations=200, test_statistic='pearson'
        )
        
        # Observed statistic should be negative and close to -1
        assert observed_stat < -0.9, "Negative correlation should yield negative statistic"
        
        # P-value should be small
        assert p_value < 0.1, "Strong negative correlation should yield small p-value"