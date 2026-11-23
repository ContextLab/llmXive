"""
Unit tests for statistical utilities in code/utils/stats.py.
"""
import numpy as np
import pytest
import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from utils.stats import apply_fdr_correction, permutation_test

class TestApplyFDRCorrection:
    def test_fdr_basic(self):
        """Test FDR correction with a standard set of p-values."""
        p_values = [0.01, 0.04, 0.03, 0.005, 0.50]
        reject, p_corrected = apply_fdr_correction(p_values, alpha=0.05)
        
        assert len(reject) == len(p_values)
        assert len(p_corrected) == len(p_values)
        
        # Check that corrected p-values are generally larger than raw
        assert all(p_corrected >= np.array(p_values))

    def test_fdr_empty(self):
        """Test FDR correction with empty input."""
        p_values = []
        reject, p_corrected = apply_fdr_correction(p_values)
        
        assert len(reject) == 0
        assert len(p_corrected) == 0

    def test_fdr_all_significant(self):
        """Test FDR correction where all p-values are significant."""
        p_values = [0.001, 0.002, 0.003]
        reject, p_corrected = apply_fdr_correction(p_values, alpha=0.05)
        
        assert all(reject)

    def test_fdr_none_significant(self):
        """Test FDR correction where no p-values are significant."""
        p_values = [0.4, 0.5, 0.6]
        reject, p_corrected = apply_fdr_correction(p_values, alpha=0.05)
        
        assert not any(reject)

class TestPermutationTest:
    def test_permutation_greater(self):
        """Test permutation test with 'greater' alternative."""
        observed = 2.5
        # Create a null distribution centered around 0
        null_dist = np.random.normal(0, 1, 10000)
        
        p_value = permutation_test(observed, null_dist, alternative='greater')
        
        assert 0 <= p_value <= 1
        # With observed=2.5 and mean=0, p-value should be small
        assert p_value < 0.05

    def test_permutation_less(self):
        """Test permutation test with 'less' alternative."""
        observed = -2.5
        null_dist = np.random.normal(0, 1, 10000)
        
        p_value = permutation_test(observed, null_dist, alternative='less')
        
        assert 0 <= p_value <= 1
        assert p_value < 0.05

    def test_permutation_two_sided(self):
        """Test permutation test with 'two-sided' alternative."""
        observed = 2.5
        null_dist = np.random.normal(0, 1, 10000)
        
        p_value = permutation_test(observed, null_dist, alternative='two-sided')
        
        assert 0 <= p_value <= 1

    def test_permutation_empty_null(self):
        """Test that permutation test raises error on empty null distribution."""
        observed = 1.0
        null_dist = np.array([])
        
        with pytest.raises(ValueError, match="Null distribution cannot be empty"):
            permutation_test(observed, null_dist)

    def test_permutation_small_null(self):
        """Test permutation test with null distribution smaller than requested permutations."""
        observed = 2.0
        null_dist = np.array([1.0, 1.5, 2.5, 3.0]) # 4 items
        
        # Should not raise, but warn (we can't easily capture the log in this simple test,
        # but we can check it runs and returns a value)
        p_value = permutation_test(observed, null_dist, n_permutations=1000)
        
        assert 0 <= p_value <= 1

    def test_permutation_invalid_alternative(self):
        """Test that permutation test raises error on invalid alternative."""
        observed = 1.0
        null_dist = np.random.normal(0, 1, 100)
        
        with pytest.raises(ValueError, match="Unknown alternative hypothesis"):
            permutation_test(observed, null_dist, alternative='invalid')