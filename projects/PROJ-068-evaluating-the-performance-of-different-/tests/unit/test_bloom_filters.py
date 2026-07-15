"""
Unit tests for Bloom Filter implementations.

This module contains contract tests and specific unit tests for the
Bloom Filter data structures, focusing on interface consistency and
false positive rate calculation accuracy.
"""
import pytest
import math
import sys
import os
import numpy as np

# Add the code directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from bloom_filters.base import (
    BloomFilter, 
    calculate_optimal_parameters, 
    get_config_for_sizes,
    FPR_TARGETS
)
from bloom_filters.hash_utils import get_k_hashes, hash_murmur3_32
from bloom_filters.config import FPR_TARGETS as CONFIG_FPR_TARGETS

# Import implementations to test
from bloom_filters.array_impl import ArrayBloomFilter
from bloom_filters.vector_impl import VectorBloomFilter
from bloom_filters.bitset_impl import BitsetBloomFilter

# Constants for testing
TEST_SEED = 42
TEST_SIZES = [1000, 10000, 100000]
TEST_FPRS = [0.01, 0.05, 0.10]


def generate_test_data(n_elements, seed=TEST_SEED):
    """Generate deterministic test data for Bloom Filter operations."""
    rng = np.random.default_rng(seed)
    # Generate random integers to simulate unique items
    # Using a large range to minimize collisions in the test data itself
    return rng.integers(0, 2**32, size=n_elements)


class TestFalsePositiveRateAccuracy:
    """
    Unit tests for false positive rate calculation accuracy.
    
    These tests verify that the implemented Bloom Filters achieve
    the target false positive rates within acceptable statistical bounds.
    """

    @pytest.mark.parametrize("fpr_target", TEST_FPRS)
    @pytest.mark.parametrize("size", [1000])  # Keep small for fast CI
    def test_fpr_accuracy_array_impl(self, size, fpr_target):
        """Test FPR accuracy for ArrayBloomFilter."""
        self._run_fpr_test(ArrayBloomFilter, size, fpr_target)

    @pytest.mark.parametrize("fpr_target", TEST_FPRS)
    @pytest.mark.parametrize("size", [1000])
    def test_fpr_accuracy_vector_impl(self, size, fpr_target):
        """Test FPR accuracy for VectorBloomFilter."""
        self._run_fpr_test(VectorBloomFilter, size, fpr_target)

    @pytest.mark.parametrize("fpr_target", TEST_FPRS)
    @pytest.mark.parametrize("size", [1000])
    def test_fpr_accuracy_bitset_impl(self, size, fpr_target):
        """Test FPR accuracy for BitsetBloomFilter."""
        self._run_fpr_test(BitsetBloomFilter, size, fpr_target)

    def _run_fpr_test(self, impl_class, n_insert, fpr_target, n_trials=10):
        """
        Run statistical test for false positive rate accuracy.
        
        Args:
            impl_class: The Bloom Filter implementation class to test.
            n_insert: Number of elements to insert.
            fpr_target: Target false positive rate.
            n_trials: Number of independent trials to average over.
        """
        rng = np.random.default_rng(TEST_SEED)
        
        observed_fprs = []
        
        for trial in range(n_trials):
            # Calculate optimal parameters for this trial
            k, m = calculate_optimal_parameters(n_insert, fpr_target)
            
            # Create filter instance
            # We pass k and m explicitly to ensure we are testing the math
            # The constructor should accept these or calculate them internally
            # Based on T015, the constructor should receive FPR targets
            try:
                # Attempt to instantiate with explicit parameters if supported
                # If not, we rely on the constructor calculating from n and fpr
                if impl_class == ArrayBloomFilter:
                    bf = impl_class(n=n_insert, fpr=fpr_target)
                elif impl_class == VectorBloomFilter:
                    bf = impl_class(n=n_insert, fpr=fpr_target)
                elif impl_class == BitsetBloomFilter:
                    bf = impl_class(n=n_insert, fpr=fpr_target)
                else:
                    pytest.fail(f"Unknown implementation class: {impl_class}")
            except TypeError:
                # Fallback if signature differs, though T015 mandates specific interface
                pytest.fail(f"Implementation {impl_class} does not accept expected n/fpr arguments.")

            # Verify internal parameters match theoretical expectations
            # Allow small floating point differences
            assert bf.m >= m, f"Bit array size {bf.m} is less than optimal {m}"
            assert bf.k == k, f"Hash count {bf.k} does not match optimal {k}"

            # Insert elements
            insert_data = generate_test_data(n_insert, seed=TEST_SEED + trial)
            for item in insert_data:
                bf.insert(item)

            # Generate query data (non-inserted items)
            # We need enough queries to get a statistically significant FPR estimate
            n_queries = max(10000, n_insert * 10)
            query_data = generate_test_data(n_queries, seed=TEST_SEED + 1000 + trial)
            
            # Filter out any accidental collisions with inserted data
            # (Very unlikely with 2^32 range, but good practice)
            query_data = [x for x in query_data if x not in insert_data]
            if len(query_data) < n_queries * 0.9:
                # Regenerate if too many collisions
                query_data = generate_test_data(n_queries, seed=TEST_SEED + 2000 + trial)
                query_data = [x for x in query_data if x not in insert_data]

            # Count false positives
            false_positives = 0
            for item in query_data:
                if bf.contains(item):
                    false_positives += 1

            trial_fpr = false_positives / len(query_data)
            observed_fprs.append(trial_fpr)

        # Calculate statistics
        mean_fpr = np.mean(observed_fprs)
        std_fpr = np.std(observed_fprs)
        
        # Theoretical bound: FPR should be close to target
        # We allow a margin of error. For 10000 queries, standard error is ~sqrt(p(1-p)/n)
        # For p=0.01, se ~ 0.001. We allow 3 standard deviations of statistical noise
        # plus a small implementation tolerance.
        tolerance = max(0.005, 3 * (math.sqrt(fpr_target * (1-fpr_target) / (n_queries * n_trials))))
        
        # Assert that the observed FPR is within acceptable bounds of the target
        # The observed rate should not be significantly higher than the target
        assert mean_fpr <= fpr_target + tolerance, (
            f"Observed FPR ({mean_fpr:.5f}) exceeds target ({fpr_target}) "
            f"by more than tolerance ({tolerance:.5f}). "
            f"Mean: {mean_fpr:.5f}, Std: {std_fpr:.5f}, Trials: {n_trials}"
        )
        
        # Also ensure it's not absurdly low (which might indicate a bug where nothing is stored)
        # If FPR is 0, that's suspicious for a probabilistic structure unless n is tiny
        if n_insert > 100:
            assert mean_fpr > fpr_target * 0.1, (
                f"Observed FPR ({mean_fpr:.5f}) is suspiciously low. "
                f"Check if elements are actually being inserted."
            )

    def test_fpr_theoretical_vs_actual(self):
        """
        Verify that the theoretical FPR formula matches the configured parameters.
        
        Theoretical FPR: (1 - e^(-kn/m))^k
        """
        test_cases = [
            (10000, 0.01),
            (10000, 0.05),
            (100000, 0.10),
        ]

        for n, p_target in test_cases:
            k, m = calculate_optimal_parameters(n, p_target)
            
            # Calculate theoretical FPR using the standard formula
            # p = (1 - e^(-kn/m))^k
            theoretical_fpr = (1 - math.exp(-k * n / m)) ** k
            
            # The calculated parameters should yield a theoretical FPR very close to target
            # Due to integer rounding of k and m, it might be slightly different
            assert abs(theoretical_fpr - p_target) < 0.01, (
                f"Theoretical FPR ({theoretical_fpr}) deviates significantly "
                f"from target ({p_target}) for n={n}, k={k}, m={m}"
            )

    def test_fpr_configuration_values(self):
        """Ensure FPR targets are correctly set to 0.01, 0.05, 0.10 as per T015."""
        expected_targets = {0.01, 0.05, 0.10}
        actual_targets = set(FPR_TARGETS)
        assert actual_targets == expected_targets, (
            f"FPR_TARGETS mismatch. Expected {expected_targets}, got {actual_targets}"
        )
        assert set(CONFIG_FPR_TARGETS) == expected_targets, (
            f"Config FPR_TARGETS mismatch. Expected {expected_targets}, got {set(CONFIG_FPR_TARGETS)}"
        )

class TestConsistencyAcrossImplementations:
    """
    Tests to ensure all implementations produce identical results for the same inputs.
    """

    def test_identical_membership_results(self):
        """Verify all three implementations return identical results for same queries."""
        n = 1000
        fpr = 0.01
        seed = 42

        insert_data = generate_test_data(n, seed=seed)
        query_data = generate_test_data(n * 10, seed=seed + 100)
        query_data = [x for x in query_data if x not in insert_data]

        implementations = [
            ("Array", ArrayBloomFilter(n=n, fpr=fpr)),
            ("Vector", VectorBloomFilter(n=n, fpr=fpr)),
            ("Bitset", BitsetBloomFilter(n=n, fpr=fpr)),
        ]

        # Insert data into all
        for name, bf in implementations:
            for item in insert_data:
                bf.insert(item)

        # Check consistency
        reference_results = {item: implementations[0][1].contains(item) for item in query_data}
        
        for name, bf in implementations[1:]:
            for item in query_data:
                result = bf.contains(item)
                assert result == reference_results[item], (
                    f"Inconsistency detected: {name} returned {result} "
                    f"while reference returned {reference_results[item]} for item {item}"
                )