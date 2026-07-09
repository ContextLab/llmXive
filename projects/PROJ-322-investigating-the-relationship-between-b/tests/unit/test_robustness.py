"""
Unit tests for the robustness module (T026).

Tests:
1. test_permutation_pvalue_is_less_than_parametric_pvalue_for_known_signal
   - Generates synthetic data with a known, strong correlation signal.
   - Computes parametric p-value and permutation p-value.
   - Asserts that the permutation p-value is <= parametric p-value (robustness check).
2. test_permutation_iterations_match_input_parameter
   - Verifies that the permutation test performs exactly the number of iterations
     specified in the input arguments.
"""

import pytest
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock

# Import the function to test. 
# We import the specific function perform_permutation_test from robustness.py
# based on the API surface provided in the project context.
from robustness import perform_permutation_test


class TestPermutationTest:
    """Unit tests for perform_permutation_test function."""

    def test_permutation_pvalue_is_less_than_parametric_pvalue_for_known_signal(self):
        """
        Test that for a dataset with a known strong signal, the permutation p-value
        is generally less than or equal to the parametric p-value, demonstrating
        the robustness of the permutation test against distributional assumptions.
        """
        # Set a fixed seed for reproducibility of the "known signal" generation
        np.random.seed(42)

        # Generate synthetic data with a strong positive correlation (r ~ 0.8)
        n_samples = 100
        x = np.random.normal(0, 1, n_samples)
        # y is strongly correlated with x plus small noise
        y = 2.5 * x + np.random.normal(0, 0.5, n_samples)

        # Create a DataFrame as expected by the function (based on typical usage in robustness.py)
        # We assume the function expects columns 'x' and 'y' or similar, 
        # but since we are testing the core logic, we pass arrays directly if the signature allows,
        # or construct a minimal dataframe if the implementation expects it.
        # Looking at the API surface: `perform_permutation_test` is a public name.
        # We will assume it takes (observed_x, observed_y, n_permutations, random_state).
        
        n_permutations = 1000
        random_state = 42

        # Run the permutation test
        # The function should return the observed statistic, the null distribution, and the p-value.
        # We mock the internal correlation calculation if needed, but here we assume real execution.
        try:
            observed_stat, null_distribution, perm_p_value = perform_permutation_test(
                x, y, n_permutations=n_permutations, random_state=random_state
            )
        except Exception as e:
            # If the function signature is different, we might need to adjust.
            # However, based on standard implementations:
            pytest.fail(f"perform_permutation_test failed with: {e}")

        # Calculate parametric p-value for comparison (Pearson correlation)
        # Using scipy.stats for the parametric baseline
        from scipy.stats import pearsonr
        _, parametric_p_value = pearsonr(x, y)

        # Assertion: The permutation p-value should be <= parametric p-value 
        # for a strong signal (this is a probabilistic check, but with 1000 permutations 
        # and strong signal, it should hold true consistently).
        # Note: In some rare cases, they might be very close, but perm_p <= param_p 
        # is the expected behavior for robust detection of strong signals.
        # To be strictly deterministic for the test, we check if perm_p is reasonably low.
        # However, the prompt asks for "less than parametric".
        
        # Since we used a fixed seed and strong signal, we expect a very low p-value for both.
        # The test asserts the relationship holds.
        assert perm_p_value <= parametric_p_value, \
            f"Permutation p-value ({perm_p_value}) should be <= parametric p-value ({parametric_p_value}) for strong signal."
        
        # Additional sanity check: p-values should be small for strong signal
        assert perm_p_value < 0.05, "Permutation p-value should be significant for strong signal."
        assert parametric_p_value < 0.05, "Parametric p-value should be significant for strong signal."


    def test_permutation_iterations_match_input_parameter(self):
        """
        Test that the number of permutations performed matches the input parameter.
        """
        np.random.seed(123)
        n_samples = 50
        x = np.random.normal(0, 1, n_samples)
        y = np.random.normal(0, 1, n_samples)

        # Test with specific iteration counts
        test_iterations = [100, 500, 1000]

        for n_iter in test_iterations:
            # We need to capture the null distribution to verify its length
            # The function returns (observed_stat, null_distribution, p_value)
            observed_stat, null_distribution, p_value = perform_permutation_test(
                x, y, n_permutations=n_iter, random_state=42
            )

            # The length of the null distribution should equal n_permutations
            assert len(null_distribution) == n_iter, \
                f"Expected {n_iter} permutations, but got {len(null_distribution)}."
            
            # Verify the p-value is calculated correctly based on the count
            # p_value = (count >= observed) / (n + 1) usually, or count / n
            # We just check the length consistency as the primary artifact of the iteration count.
            assert isinstance(p_value, float), "P-value should be a float."