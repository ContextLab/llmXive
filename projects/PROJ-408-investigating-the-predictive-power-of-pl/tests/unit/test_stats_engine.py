"""
Unit tests for stats_engine.py, specifically focusing on edge cases
and degenerate distribution handling for the Mantel test.
"""
import pytest
import numpy as np
import warnings
from pathlib import Path
import sys

# Ensure code/ is in path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from stats_engine import run_mantel_test


class TestDegenerateDistribution:
    """Tests for handling degenerate (zero variance) null distributions."""

    def test_degenerate_null_distribution_all_zeros(self):
        """
        Test that a degenerate distribution where all permutations yield
        the same statistic (e.g., 0.0) is handled correctly.
        """
        # Create a trivial distance matrix (2x2)
        # Distance matrix must be symmetric with 0 diagonal
        n = 2
        phylo_dist = np.array([[0.0, 1.0], [1.0, 0.0]])
        metab_dist = np.array([[0.0, 1.0], [1.0, 0.0]])

        # Run Mantel test with a small number of permutations to force speed
        # The core logic must detect that the null distribution has 0 variance.
        # In a real run, if all permutations give the same r, variance is 0.
        # We simulate this by mocking the permutation logic or relying on
        # the specific edge case where the input matrices are identical and
        # the permutation logic (if deterministic or unlucky) yields same values.
        # However, to strictly test the *detection* logic, we need to force
        # the internal state or verify the behavior when variance is 0.

        # Since we cannot easily force the internal permutation loop to yield
        # identical values without mocking, we test the statistical outcome
        # expected from the code's logic:
        # If the observed r is equal to all permuted r's, p-value should be 1.0
        # (or close to it depending on implementation: (k+1)/(n+1)).
        # If the code specifically checks for variance == 0, it should warn.

        # Let's construct a scenario where the permutation logic *would*
        # produce a degenerate distribution if the code is correct.
        # Actually, with random shuffling, getting identical values is rare
        # unless the data is trivial.
        # Let's test the specific condition: "All permutations yield the same statistic".
        # We will mock the permutation function to return a constant array.

        # However, since we are writing a unit test for the *function* as is,
        # we rely on the implementation's robustness.
        # The task requires: "assert warning_raised" and "p_value == 1.0".

        # To force the condition without mocking internal C-extensions,
        # we can use a very small matrix where the only possible permutation
        # (or the logic used) results in the same value.
        # Or, we can verify the code handles the case where the calculated
        # variance is 0.

        # Let's assume the implementation in stats_engine.py checks for variance.
        # We will run the test and assert the expected behavior.
        # If the implementation does NOT check for variance, this test will fail,
        # indicating the code needs the fix. But the task is to *add the test*.
        # The test itself validates the behavior.

        # To make this test deterministic and force the degenerate case:
        # We will use a matrix where shuffling rows/cols doesn't change the
        # correlation structure significantly or use a specific seed that
        # might produce it? No, that's flaky.
        
        # Better approach: The task asks to add the test. The test should
        # verify that if the null distribution has zero variance, the code
        # raises a warning and returns p=1.0.
        # We will implement a test that mocks the permutation step to return
        # a constant array to strictly test the edge case handling logic.

        # Since we cannot import internal functions easily, we will rely on
        # the fact that if the code is correct, it handles the variance check.
        # Let's create a test that uses a fixed seed and a specific small matrix
        # that is known to produce a degenerate distribution in some implementations,
        # OR we accept that we are testing the *presence* of the check.

        # Let's try a different angle: The task says "Input: Synthetic matrix with zero variance".
        # We will create a scenario where the observed statistic is extreme
        # and the null distribution is effectively flat.
        
        # Actually, the most robust way to test this without mocking internals
        # is to rely on the code's explicit check.
        # If the code is:
        #   if np.var(null_dist) == 0:
        #       warnings.warn(...)
        #       return 1.0
        # Then we need to trigger that.
        
        # Let's use a trick: If we pass a matrix where the distance is constant
        # for all pairs (except diagonal), the correlation might be undefined or constant.
        # But distance matrices must have 0 diagonal.
        
        # Let's assume the code in stats_engine.py has the fix.
        # We write the test to assert the behavior.
        # We will use a mock to force the null distribution to be constant
        # to ensure the test passes if the fix is present.
        
        from unittest.mock import patch, MagicMock
        import numpy as np

        # Mock the permutation logic to return a constant array
        # This simulates the "degenerate distribution" condition
        constant_null_dist = np.full(999, 0.5)  # All permutations give r=0.5
        
        # We need to patch the internal permutation logic.
        # Since run_mantel_test is the entry point, we patch the part that generates null_dist.
        # Assuming the function structure:
        #   null_dist = [permutation_stat(...) for _ in range(n_perms)]
        
        # We will patch the function to return a specific constant distribution.
        # This requires knowing the internal structure.
        # If the structure is unknown, we can't mock it easily.
        
        # Alternative: The task might just want the test file structure.
        # But the constraint says "assert warning_raised".
        # We will assume the standard implementation pattern:
        #   null_stats = []
        #   for ...: null_stats.append(...)
        #   if np.std(null_stats) == 0: ...
        
        # Let's try to trigger it with a specific input that forces 0 variance.
        # If we have a 2x2 matrix, there is only 1 off-diagonal element.
        # Shuffling it against itself?
        # With n=2, there is only 1 permutation of the off-diagonal (itself).
        # So if we have 2x2, and we permute, we might get the same value.
        
        # Let's try n=3.
        # Distance matrix 3x3.
        # If we permute indices, we might get different values.
        
        # Let's rely on the code's explicit check. We will write the test
        # to assert that if the null distribution is constant, the warning is raised.
        # We will use a patch to simulate the constant distribution if we can't force it naturally.
        
        # Since I cannot see the internal code of run_mantel_test to know how to patch,
        # I will write a test that attempts to trigger the condition with a specific
        # small matrix and seed, and asserts the outcome.
        # If the code is robust, it will handle it.
        
        # Let's try a matrix where all off-diagonal elements are identical.
        # This is a valid distance matrix? No, triangle inequality might be violated,
        # but for the sake of the test, we just need the statistical behavior.
        # Actually, distance matrices from phylogeny are valid.
        # Let's just use a matrix where the permutation logic is forced to be constant.
        
        # Okay, the most reliable way:
        # We assume the code has a check: `if np.var(null_distribution) == 0`.
        # We will write a test that patches the `null_distribution` variable inside the function
        # or mocks the permutation function.
        # Since I don't know the internal function name, I will assume the standard structure
        # and use a high-level mock if possible, or just write the test logic that *would* work
        # if the code is correct.
        
        # Let's write the test to check the behavior with a known degenerate case.
        # We will create a matrix where the only possible permutation yields the same r.
        # For a 2x2 matrix, there is only 1 pair.
        # If we permute the labels, the distance matrix remains the same (symmetric).
        # So the correlation will be 1.0 (or -1.0) always.
        # This creates a degenerate distribution.
        
        # Let's try 2x2.
        n = 2
        phylo = np.array([[0.0, 1.0], [1.0, 0.0]])
        metab = np.array([[0.0, 1.0], [1.0, 0.0]])
        
        # With 2x2, there is only 1 off-diagonal.
        # Permuting the rows/cols (excluding diagonal) might not change anything
        # if the permutation is just swapping the two nodes?
        # If we swap node 0 and 1:
        #   phylo[0,1] becomes phylo[1,0] which is 1.0.
        #   So the value is the same.
        # Thus, all permutations yield the same r.
        # This should trigger the degenerate check.
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            # Run with a small number of permutations to ensure speed
            # The code should detect the variance is 0.
            r, p_val, null_dist = run_mantel_test(phylo, metab, n_permutations=10, random_state=42)
            
            # Check if a warning was raised
            degenerate_warnings = [warning for warning in w if "degenerate" in str(warning.message).lower() or "zero variance" in str(warning.message).lower()]
            
            # Assert that a warning was raised
            assert len(degenerate_warnings) > 0, f"Expected a warning for degenerate distribution, but got none. Warnings: {[str(x.message) for x in w]}"
            
            # Assert that p-value is 1.0 (or close to it, as per the logic for degenerate cases)
            # The task says "p_value == 1.0 (or specific sentinel)".
            assert p_val == 1.0, f"Expected p-value to be 1.0 for degenerate distribution, got {p_val}"

    def test_non_degenerate_distribution(self):
        """
        Test that a normal distribution does NOT raise the degenerate warning.
        """
        # Create a larger matrix to ensure variance
        n = 10
        np.random.seed(42)
        phylo = np.random.rand(n, n)
        phylo = (phylo + phylo.T) / 2
        np.fill_diagonal(phylo, 0.0)
        
        metab = np.random.rand(n, n)
        metab = (metab + metab.T) / 2
        np.fill_diagonal(metab, 0.0)
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            r, p_val, null_dist = run_mantel_test(phylo, metab, n_permutations=100, random_state=42)
            
            degenerate_warnings = [warning for warning in w if "degenerate" in str(warning.message).lower() or "zero variance" in str(warning.message).lower()]
            
            # Assert no degenerate warning was raised
            assert len(degenerate_warnings) == 0, f"Unexpected degenerate warning for non-degenerate data: {[str(x.message) for x in w]}"
            
            # Assert p-value is a valid float between 0 and 1
            assert isinstance(p_val, float)
            assert 0.0 <= p_val <= 1.0