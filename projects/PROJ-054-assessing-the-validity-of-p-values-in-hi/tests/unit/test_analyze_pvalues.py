"""
Unit tests for the permutation test generator in code/analyze_pvalues.py.
"""
import pytest
import numpy as np
from scipy import stats

from code.analyze_pvalues import generate_permutation_reference, calculate_ks_statistic
from code.utils.exceptions import AnalysisError


class TestPermutationReference:
    """Tests for the Gold Standard permutation test generator."""

    def test_output_structure(self):
        """Verify that the function returns the expected dictionary keys."""
        data = np.random.randn(50, 20)
        result = generate_permutation_reference(data, n_permutations=10, seed=42)

        expected_keys = {
            'observed_stats', 'permuted_stats', 'p_values', 
            'n_permutations', 'shape', 'seed', 'two_sided'
        }
        assert set(result.keys()) == expected_keys

    def test_permuted_stats_shape(self):
        """Verify that permuted stats have the correct shape."""
        n_samples, n_features = 100, 15
        n_perms = 50
        data = np.random.randn(n_samples, n_features)
        
        result = generate_permutation_reference(data, n_permutations=n_perms, seed=99)
        
        # permuted_stats should be a list of lists (n_perms, n_features)
        # or converted to array in the logic, but stored as list in dict
        assert len(result['permuted_stats']) == n_perms
        assert len(result['permuted_stats'][0]) == n_features

    def test_p_value_range(self):
        """Verify that p-values are within [0, 1]."""
        data = np.random.randn(50, 10)
        result = generate_permutation_reference(data, n_permutations=20, seed=1)
        
        p_vals = result['p_values']
        assert all(0.0 <= p <= 1.0 for p in p_vals)

    def test_invalid_input_shape(self):
        """Verify that non-2D input raises AnalysisError."""
        data_1d = np.random.randn(100)
        with pytest.raises(AnalysisError):
            generate_permutation_reference(data_1d)

    def test_insufficient_samples(self):
        """Verify that data with < 2 samples raises AnalysisError."""
        data = np.random.randn(1, 10)
        with pytest.raises(AnalysisError):
            generate_permutation_reference(data)

    def test_deterministic_with_seed(self):
        """Verify that results are reproducible with the same seed."""
        data = np.random.randn(50, 10)
        seed = 12345
        
        res1 = generate_permutation_reference(data, n_permutations=10, seed=seed)
        res2 = generate_permutation_reference(data, n_permutations=10, seed=seed)
        
        assert res1['p_values'] == res2['p_values']
        assert res1['observed_stats'] == res2['observed_stats']


class TestKSStatistic:
    """Tests for the KS statistic calculation."""

    def test_ks_uniform_perfect(self):
        """
        Test KS statistic on a perfect uniform distribution (simulated).
        With large N, KS should be small.
        """
        # Generate uniform random numbers
        p_vals = np.random.uniform(0, 1, 10000)
        ks = calculate_ks_statistic(list(p_vals))
        
        # For N=10000, KS should be roughly < 0.02 (approx 1.36/sqrt(N) at 95%)
        assert ks < 0.03

    def test_ks_non_uniform(self):
        """Test KS statistic on a clearly non-uniform distribution."""
        # Generate p-values that are clustered near 0 (anti-conservative)
        # e.g., Beta(0.5, 1) distribution which is skewed towards 0
        p_vals = np.random.beta(0.5, 1, 1000)
        ks = calculate_ks_statistic(list(p_vals))
        
        # Should be significantly larger than for uniform
        assert ks > 0.05

    def test_empty_input(self):
        """Verify that empty input raises AnalysisError."""
        with pytest.raises(AnalysisError):
            calculate_ks_statistic([])

    def test_one_vs_two_sided_logic(self):
        """
        Verify that the function handles the logic correctly.
        This is a structural test since KS implementation is fixed to uniform.
        """
        p_vals = [0.1, 0.2, 0.3, 0.8, 0.9]
        # Just ensure it runs without error
        ks = calculate_ks_statistic(p_vals)
        assert isinstance(ks, float)
        assert 0.0 <= ks <= 1.0
