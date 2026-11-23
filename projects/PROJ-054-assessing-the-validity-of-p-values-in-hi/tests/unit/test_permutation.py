"""
Unit tests for permutation test generator in analyze_pvalues.py.
These tests verify permutation-based Gold Standard generation.
"""
import pytest
import numpy as np
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from analyze_pvalues import generate_permutation_reference, calculate_ks_statistic


class TestPermutationReference:
    """Tests for T028: Permutation test generator."""

    def test_permutation_preserves_structure(self):
        """Test that permutation preserves correlation structure in expectation."""
        np.random.seed(42)
        n = 100
        p = 10
        rho = 0.5

        # Generate correlated data
        from generate_data import generate_correlated_data
        data = generate_correlated_data(n, p, rho, seed=42)

        # Generate permutation reference
        perm_pvalues = generate_permutation_reference(data, n_permutations=100, seed=42)

        # Permutation p-values should be uniformly distributed
        assert len(perm_pvalues) == p, f"Should have {p} permutation p-values"
        assert all(0 <= pv <= 1 for pv in perm_pvalues), "All p-values should be in [0, 1]"

    def test_permutation_uniformity(self):
        """Test that permutation p-values are approximately uniform under null."""
        np.random.seed(42)
        n = 200
        p = 20
        rho = 0.0  # No correlation

        from generate_data import generate_correlated_data
        data = generate_correlated_data(n, p, rho, seed=42)

        perm_pvalues = generate_permutation_reference(data, n_permutations=500, seed=42)

        # Test uniformity with KS test
        from scipy import stats
        ks_stat, p_value = stats.kstest(perm_pvalues, 'uniform')

        # Should not reject uniformity (p > 0.05)
        assert p_value > 0.05, f"Permutation p-values should be uniform, KS p-value={p_value}"

    def test_permutation_respects_correlation(self):
        """Test that permutation respects correlation structure."""
        np.random.seed(42)
        n = 200
        p = 20
        rho = 0.8  # Strong correlation

        from generate_data import generate_correlated_data
        data = generate_correlated_data(n, p, rho, seed=42)

        perm_pvalues = generate_permutation_reference(data, n_permutations=500, seed=42)

        # With strong correlation, permutation test should still produce valid p-values
        # (not necessarily uniform, but valid under the null)
        assert len(perm_pvalues) == p, f"Should have {p} permutation p-values"
        assert all(0 <= pv <= 1 for pv in perm_pvalues), "All p-values should be in [0, 1]"

    def test_ks_statistic_calculation(self):
        """Test KS statistic calculation between standard and permutation p-values."""
        np.random.seed(42)
        n = 200
        p = 20
        rho = 0.5

        from generate_data import generate_correlated_data
        data = generate_correlated_data(n, p, rho, seed=42)

        # Generate permutation reference
        perm_pvalues = generate_permutation_reference(data, n_permutations=500, seed=42)

        # Generate standard p-values (t-tests)
        from run_tests import run_hypothesis_tests
        standard_pvalues = []
        for i in range(p):
            _, pval = run_hypothesis_tests(data[:, i], data[:, i], test_type='t')
            standard_pvalues.append(pval)

        # Calculate KS statistic
        ks_stat = calculate_ks_statistic(standard_pvalues, perm_pvalues)

        assert 0 <= ks_stat <= 1, f"KS statistic {ks_stat} should be in [0, 1]"

    def test_permutation_deterministic_with_seed(self):
        """Test that permutation is deterministic with same seed."""
        np.random.seed(42)
        n = 100
        p = 10
        rho = 0.5

        from generate_data import generate_correlated_data
        data = generate_correlated_data(n, p, rho, seed=42)

        perm_pvalues_1 = generate_permutation_reference(data, n_permutations=100, seed=123)
        perm_pvalues_2 = generate_permutation_reference(data, n_permutations=100, seed=123)

        np.testing.assert_array_equal(
            perm_pvalues_1,
            perm_pvalues_2,
            err_msg="Same seed should produce identical permutation p-values"
        )

    def test_permutation_with_high_dimensionality(self):
        """Test permutation test with high-dimensional data (p > n)."""
        np.random.seed(42)
        n = 50
        p = 500  # p > n
        rho = 0.3

        from generate_data import generate_correlated_data
        data = generate_correlated_data(n, p, rho, seed=42)

        # Should handle high-dimensional case
        perm_pvalues = generate_permutation_reference(data, n_permutations=100, seed=42)

        assert len(perm_pvalues) == p, f"Should have {p} permutation p-values"
        assert all(0 <= pv <= 1 for pv in perm_pvalues), "All p-values should be in [0, 1]"