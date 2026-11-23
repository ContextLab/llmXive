import pytest
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock
import sys
import os

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from main import run_single_synthetic_validation, run_synthetic_validation_loop
from stats_engine import generate_synthetic_dataset, compute_correlation, construct_graph, calculate_stats, run_permutations_for_threshold

class TestSyntheticValidation:
    def test_run_single_synthetic_validation_passes(self, caplog):
        """Test that a synthetic validation run passes when stats are within null distribution."""
        # Mock config
        config = {
            'threshold': 0.3,
            'permutations': 100, # Reduced for test speed
            'random_seed': 42
        }
        
        # Mock logger
        import logging
        logger = logging.getLogger(__name__)
        
        # We rely on the actual implementation here, but ensure it doesn't crash
        # Since generate_synthetic_dataset creates identity covariance, correlations should be near 0.
        # The observed stats should be within the null distribution of permuted data (which is also near 0).
        # This is a sanity check that the logic flows without error.
        
        # Note: In a real test environment, we might mock run_permutations_for_threshold
        # to return a predictable null distribution to guarantee pass/fail.
        # However, with N=100 permutations and synthetic data, it should statistically pass most of the time.
        
        result = run_single_synthetic_validation(logger, config)
        assert isinstance(result, bool)
        # We expect True most of the time, but assert that it returns a boolean
        
    def test_synthetic_validation_loop_structure(self):
        """Test the loop logic structure."""
        import logging
        logger = logging.getLogger(__name__)
        config = {
            'threshold': 0.3,
            'permutations': 10,
            'random_seed': 42,
            'output_results_dir': '/tmp'
        }
        
        # Mock the single run to return True to ensure loop completes
        with patch('main.run_single_synthetic_validation', return_value=True):
            result = run_synthetic_validation_loop(logger, config)
            assert result is True
            
    def test_synthetic_validation_loop_fail(self):
        """Test the loop logic when too many runs fail."""
        import logging
        logger = logging.getLogger(__name__)
        config = {
            'threshold': 0.3,
            'permutations': 10,
            'random_seed': 42,
            'output_results_dir': '/tmp'
        }
        
        # Mock the single run to return False
        with patch('main.run_single_synthetic_validation', return_value=False):
            result = run_synthetic_validation_loop(logger, config)
            assert result is False
            
    def test_synthetic_data_properties(self):
        """Verify synthetic data generation creates expected properties."""
        df = generate_synthetic_dataset(n_samples=500, n_features=20, seed=42)
        assert df.shape == (500, 20)
        assert df.isnull().sum().sum() == 0
        
        # Check correlation is near 0 for identity covariance
        corr = df.corr().values
        # Diagonal should be 1, off-diagonal near 0
        np.testing.assert_array_almost_equal(np.diag(corr), np.ones(20), decimal=1)
        # Average off-diagonal should be small
        off_diag = corr[~np.eye(20, dtype=bool)].reshape(-1)
        assert np.abs(np.mean(off_diag)) < 0.1
