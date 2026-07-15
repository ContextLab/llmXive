"""
Unit tests for statistical analysis functions, specifically Point-Biserial correlation.

This module tests the calculation of Point-Biserial correlation coefficients,
which measure the relationship between a binary variable (success/failure)
and a continuous variable (nodes_visited).
"""

import pytest
import numpy as np
from typing import List, Tuple
import sys
import os

# Add parent directory to path for imports during local testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.analysis.stats import point_biserial_correlation


class TestPointBiserialCorrelation:
    """Test suite for point_biserial_correlation function."""

    def test_basic_correlation_positive(self):
        """Test basic positive correlation calculation."""
        # Binary variable: 0 = failure, 1 = success
        # Continuous variable: nodes_visited
        # Expecting positive correlation (more nodes visited -> higher success)
        binary = np.array([0, 0, 0, 1, 1, 1, 1])
        continuous = np.array([5, 6, 7, 10, 12, 13, 15])
        
        r_pb, p_value = point_biserial_correlation(binary, continuous)
        
        assert isinstance(r_pb, float), "Correlation coefficient should be a float"
        assert isinstance(p_value, float), "P-value should be a float"
        assert -1.0 <= r_pb <= 1.0, "Correlation coefficient must be between -1 and 1"
        assert r_pb > 0, "Expected positive correlation in this test case"
        assert 0 <= p_value <= 1.0, "P-value must be between 0 and 1"

    def test_basic_correlation_negative(self):
        """Test negative correlation calculation."""
        # Binary variable: 0 = success, 1 = failure
        # Continuous variable: nodes_visited
        # Expecting negative correlation (more nodes visited -> lower success)
        binary = np.array([1, 1, 1, 0, 0, 0, 0])
        continuous = np.array([5, 6, 7, 10, 12, 13, 15])
        
        r_pb, p_value = point_biserial_correlation(binary, continuous)
        
        assert r_pb < 0, "Expected negative correlation in this test case"
        assert -1.0 <= r_pb <= 1.0, "Correlation coefficient must be between -1 and 1"

    def test_perfect_correlation(self):
        """Test perfect correlation case."""
        # Perfect separation: all 0s have low values, all 1s have high values
        binary = np.array([0, 0, 0, 1, 1, 1])
        continuous = np.array([1, 2, 3, 10, 11, 12])
        
        r_pb, p_value = point_biserial_correlation(binary, continuous)
        
        # Should be close to 1.0 (perfect positive correlation)
        assert abs(r_pb) > 0.95, f"Expected near-perfect correlation, got {r_pb}"

    def test_no_correlation(self):
        """Test case with no correlation."""
        # Binary variable
        binary = np.array([0, 0, 1, 1])
        # Continuous variable with same mean for both groups
        continuous = np.array([5, 15, 5, 15])
        
        r_pb, p_value = point_biserial_correlation(binary, continuous)
        
        # Should be close to 0
        assert abs(r_pb) < 0.1, f"Expected near-zero correlation, got {r_pb}"

    def test_single_group_error(self):
        """Test that error is raised when binary variable has only one unique value."""
        binary = np.array([0, 0, 0, 0])
        continuous = np.array([1, 2, 3, 4])
        
        with pytest.raises(ValueError, match="Binary variable must have exactly two unique values"):
            point_biserial_correlation(binary, continuous)

    def test_mismatched_lengths(self):
        """Test that error is raised when arrays have different lengths."""
        binary = np.array([0, 0, 1, 1])
        continuous = np.array([1, 2, 3])
        
        with pytest.raises(ValueError, match="Input arrays must have the same length"):
            point_biserial_correlation(binary, continuous)

    def test_empty_arrays(self):
        """Test that error is raised for empty arrays."""
        binary = np.array([])
        continuous = np.array([])
        
        with pytest.raises(ValueError, match="Input arrays cannot be empty"):
            point_biserial_correlation(binary, continuous)

    def test_single_element(self):
        """Test that error is raised for single element arrays."""
        binary = np.array([0])
        continuous = np.array([1])
        
        with pytest.raises(ValueError, match="Input arrays must have at least 2 elements"):
            point_biserial_correlation(binary, continuous)

    def test_realistic_scenario(self):
        """Test with realistic LoCoMo benchmark-like data."""
        # Simulating results from graph traversal tasks
        # 0 = task failed, 1 = task succeeded
        binary = np.array([0, 0, 0, 0, 1, 1, 1, 1, 1, 1])
        # Nodes visited (continuous variable)
        continuous = np.array([5, 6, 7, 8, 15, 16, 17, 18, 19, 20])
        
        r_pb, p_value = point_biserial_correlation(binary, continuous)
        
        assert r_pb > 0.5, f"Expected strong positive correlation, got {r_pb}"
        assert p_value < 0.05, f"Expected significant p-value, got {p_value}"

    def test_dtype_preservation(self):
        """Test that function handles different numpy dtypes correctly."""
        binary = np.array([0, 0, 1, 1], dtype=np.int32)
        continuous = np.array([1.0, 2.0, 3.0, 4.0], dtype=np.float64)
        
        r_pb, p_value = point_biserial_correlation(binary, continuous)
        
        assert isinstance(r_pb, float)
        assert isinstance(p_value, float)

    def test_large_dataset(self):
        """Test with a larger dataset to ensure scalability."""
        np.random.seed(42)
        n = 1000
        binary = np.random.choice([0, 1], size=n)
        # Create a correlation: higher nodes_visited for success (1)
        continuous = np.where(binary == 1, 
                             np.random.normal(20, 5, n), 
                             np.random.normal(10, 5, n))
        
        r_pb, p_value = point_biserial_correlation(binary, continuous)
        
        assert -1.0 <= r_pb <= 1.0
        assert 0 <= p_value <= 1.0
        # Should detect the correlation we created
        assert r_pb > 0.3, f"Expected to detect correlation, got {r_pb}"

    def test_edge_case_binary_balance(self):
        """Test with unbalanced binary classes."""
        # Highly unbalanced: 90% failures, 10% successes
        binary = np.array([0] * 90 + [1] * 10)
        continuous = np.array([5] * 90 + [20] * 10)
        
        r_pb, p_value = point_biserial_correlation(binary, continuous)
        
        assert abs(r_pb) > 0.8, f"Expected strong correlation despite imbalance, got {r_pb}"

    def test_output_format(self):
        """Test that output format is consistent and predictable."""
        binary = np.array([0, 0, 1, 1])
        continuous = np.array([1, 2, 3, 4])
        
        r_pb, p_value = point_biserial_correlation(binary, continuous)
        
        # Check that outputs are scalars
        assert np.isscalar(r_pb)
        assert np.isscalar(p_value)
        
        # Check that outputs are finite
        assert np.isfinite(r_pb)
        assert np.isfinite(p_value)

    def test_consistency_with_scipy(self):
        """Verify our implementation matches scipy's pointbiserialr when available."""
        try:
            from scipy.stats import pointbiserialr
            from scipy.stats import pointbiserialr as scipy_pb
            
            binary = np.array([0, 0, 1, 1, 1, 0, 1, 1])
            continuous = np.array([1, 2, 3, 4, 5, 6, 7, 8])
            
            r_pb, p_value = point_biserial_correlation(binary, continuous)
            scipy_r, scipy_p = scipy_pb(binary, continuous)
            
            # Allow small floating point differences
            assert np.isclose(r_pb, scipy_r, rtol=1e-5), \
                f"Our r_pb ({r_pb}) differs from scipy ({scipy_r})"
            assert np.isclose(p_value, scipy_p, rtol=1e-5), \
                f"Our p_value ({p_value}) differs from scipy ({scipy_p})"
        except ImportError:
            pytest.skip("scipy not available for cross-validation")