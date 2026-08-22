"""
Tests for Permutation Test (T025)
"""
import pytest
import numpy as np
import json
import os
import sys
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# Add code to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from models.permutation_test import run_permutation_test, load_loso_results, load_null_results
from utils.error_codes import ErrorCode

class TestPermutationTest:
    
    def test_permutation_test_significant_result(self):
        """
        Test that the permutation test correctly identifies a significant result
        when the RF model is clearly better than the null model.
        """
        # Create synthetic fold data where RF is consistently better
        # Null MAEs: [100, 100, 100, 100, 100]
        # RF MAEs:   [50,  50,  50,  50,  50]
        # Diff: 50.0 (Always positive)
        null_maes = [100.0] * 5
        rf_maes = [50.0] * 5
        
        results = run_permutation_test(
            rf_maes, 
            null_maes, 
            n_iterations=1000, 
            random_seed=42
        )
        
        # Since the difference is constant and positive, p-value should be 0.0 (or very close)
        assert results['p_value'] == 0.0
        assert results['significant'] is True
        assert results['observed_mean_difference'] == 50.0
        
    def test_permutation_test_non_significant_result(self):
        """
        Test that the permutation test correctly identifies a non-significant result
        when the models perform similarly.
        """
        # Create synthetic fold data where models are identical
        null_maes = [100.0, 100.0, 100.0, 100.0, 100.0]
        rf_maes = [100.0, 100.0, 100.0, 100.0, 100.0]
        
        results = run_permutation_test(
            rf_maes, 
            null_maes, 
            n_iterations=1000, 
            random_seed=42
        )
        
        # Observed difference is 0. P-value should be ~0.5 (symmetric)
        assert 0.4 <= results['p_value'] <= 0.6
        assert results['significant'] is False
        
    def test_permutation_test_random_variation(self):
        """
        Test with random data to ensure the distribution behaves as expected.
        """
        np.random.seed(123)
        null_maes = np.random.normal(100, 10, 10).tolist()
        # RF is slightly better on average but with noise
        rf_maes = [n - np.random.uniform(-5, 15) for n in null_maes] 
        
        results = run_permutation_test(
            rf_maes, 
            null_maes, 
            n_iterations=2000, 
            random_seed=42
        )
        
        # Just check that it runs and returns valid structure
        assert 'p_value' in results
        assert 'observed_mean_difference' in results
        assert 'significant' in results
        assert 0.0 <= results['p_value'] <= 1.0
        
    def test_mismatched_fold_lengths_raises_error(self):
        """
        Test that mismatched list lengths raise a ValueError.
        """
        with pytest.raises(ValueError):
            run_permutation_test([1, 2, 3], [1, 2])
            
    def test_zero_variance_handling(self):
        """
        Test handling of zero variance in differences.
        """
        # All differences are the same
        null_maes = [10.0, 10.0]
        rf_maes = [5.0, 5.0]
        
        results = run_permutation_test(
            null_maes, 
            rf_maes, 
            n_iterations=100, 
            random_seed=42
        )
        
        # Should not crash, effect size might be NaN or inf handled gracefully
        # In our implementation, we check std > 0
        assert results['p_value'] == 0.0 # Always significant if diff is constant positive
        assert results['significant'] is True

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
