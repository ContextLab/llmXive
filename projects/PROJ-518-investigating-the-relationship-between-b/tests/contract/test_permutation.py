"""Contract tests for permutation testing functionality."""
import numpy as np
from analysis.statistics import run_permutation_test


def test_permutation_counts():
    """
    Verify that run_permutation_test returns a valid p-value.

    The function should:
    1. Accept flexibility and creativity arrays.
    2. Perform the specified number of permutations.
    3. Return a float between 0 and 1.
    """
    # Create synthetic data for testing
    np.random.seed(42)
    flexibility = np.random.randn(50)
    creativity = np.random.randn(50)

    # Run permutation test with a small number of permutations for speed
    p_value = run_permutation_test(flexibility, creativity, n_permutations=100)

    # Assert p_value is a float
    assert isinstance(p_value, float), "p_value should be a float"

    # Assert p_value is in valid range [0, 1]
    assert 0.0 <= p_value <= 1.0, f"p_value {p_value} should be between 0 and 1"

    # Test that shuffling destroys correlation (with high probability)
    # Create data with known correlation
    x = np.random.randn(100)
    y = 2 * x + np.random.randn(100) * 0.5  # Strong positive correlation

    p_corr = run_permutation_test(x, y, n_permutations=1000)

    # The p-value should be small for correlated data
    assert p_corr < 0.1, f"Expected small p-value for correlated data, got {p_corr}"

    # Test with uncorrelated data
    x_uncorr = np.random.randn(100)
    y_uncorr = np.random.randn(100)

    p_uncorr = run_permutation_test(x_uncorr, y_uncorr, n_permutations=1000)

    # The p-value should be large for uncorrelated data
    assert p_uncorr > 0.05, f"Expected large p-value for uncorrelated data, got {p_uncorr}"
