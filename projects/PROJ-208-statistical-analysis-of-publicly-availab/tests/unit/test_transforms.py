"""
Unit tests for log-transform handling of zero values.
"""

import pytest
import numpy as np
from pathlib import Path
import sys

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from analysis.distribution_fitting import fit_distribution

class TestLogTransform:
    """Tests for handling zero and negative values in log-transform."""

    def test_fit_distribution_with_zeros(self):
        """Test that fit_distribution handles zero values by filtering them out."""
        data_with_zeros = np.array([0.0, 1.0, 2.0, 3.0, 4.0, 5.0])
        result = fit_distribution(data_with_zeros, 'lognorm')
        
        assert result['status'] == 'success'
        assert result['n_samples'] == 5  # Zeros should be filtered
        assert 'ks_statistic' in result
        assert 'p_value' in result
        assert 'aic' in result

    def test_fit_distribution_all_zeros(self):
        """Test that fit_distribution fails gracefully when all values are zero."""
        data_all_zeros = np.array([0.0, 0.0, 0.0, 0.0])
        result = fit_distribution(data_all_zeros, 'lognorm')
        
        assert result['status'] == 'failed'
        assert 'reason' in result

    def test_fit_distribution_with_negative_values(self):
        """Test that fit_distribution handles negative values by filtering them out."""
        data_with_negatives = np.array([-1.0, 0.0, 1.0, 2.0, 3.0])
        result = fit_distribution(data_with_negatives, 'lognorm')
        
        assert result['status'] == 'success'
        assert result['n_samples'] == 3  # Only positive values counted

    def test_fit_distribution_small_positive(self):
        """Test fitting with very small positive values."""
        data_small = np.array([0.001, 0.01, 0.1, 1.0, 10.0])
        result = fit_distribution(data_small, 'lognorm')
        
        assert result['status'] == 'success'
        assert result['n_samples'] == 5
        assert result['ks_statistic'] >= 0
        assert 0 <= result['p_value'] <= 1

    def test_fit_distribution_weibull_with_zeros(self):
        """Test Weibull fitting with zero values."""
        data_with_zeros = np.array([0.0, 1.0, 2.0, 3.0, 4.0, 5.0])
        result = fit_distribution(data_with_zeros, 'weibull_min')
        
        assert result['status'] == 'success'
        assert result['n_samples'] == 5
