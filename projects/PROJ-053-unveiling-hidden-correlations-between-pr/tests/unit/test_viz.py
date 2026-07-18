"""
Unit tests for visualization utility functions, specifically uncertainty threshold calculation.
Tests for Task T032: Unit test for uncertainty threshold calculation (2x median).
"""
import pytest
import numpy as np
import sys
import os

# Ensure the code directory is in the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from utils.viz_utils import calculate_uncertainty_threshold


class TestUncertaintyThreshold:
    """Tests for the uncertainty threshold calculation logic."""

    def test_basic_threshold_calculation(self):
        """Test that threshold is correctly calculated as 2x median."""
        uncertainties = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        median_val = np.median(uncertainties)  # 3.0
        expected_threshold = 2 * median_val  # 6.0

        result = calculate_uncertainty_threshold(uncertainties)

        assert result == expected_threshold
        assert result == 6.0

    def test_threshold_with_floats(self):
        """Test threshold calculation with floating point uncertainties."""
        uncertainties = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
        median_val = np.median(uncertainties)  # 0.3
        expected_threshold = 0.6

        result = calculate_uncertainty_threshold(uncertainties)

        assert np.isclose(result, expected_threshold)

    def test_threshold_with_duplicates(self):
        """Test threshold calculation when median is not unique."""
        uncertainties = np.array([1.0, 1.0, 1.0, 1.0, 1.0])
        median_val = np.median(uncertainties)  # 1.0
        expected_threshold = 2.0

        result = calculate_uncertainty_threshold(uncertainties)

        assert result == expected_threshold

    def test_threshold_with_even_count(self):
        """Test threshold calculation with an even number of samples."""
        uncertainties = np.array([1.0, 2.0, 3.0, 4.0])
        median_val = np.median(uncertainties)  # 2.5
        expected_threshold = 5.0

        result = calculate_uncertainty_threshold(uncertainties)

        assert result == expected_threshold

    def test_threshold_with_zeros(self):
        """Test threshold calculation when some uncertainties are zero."""
        uncertainties = np.array([0.0, 0.0, 1.0, 2.0, 3.0])
        median_val = np.median(uncertainties)  # 1.0
        expected_threshold = 2.0

        result = calculate_uncertainty_threshold(uncertainties)

        assert result == expected_threshold

    def test_single_element(self):
        """Test threshold calculation with a single element."""
        uncertainties = np.array([5.0])
        median_val = 5.0
        expected_threshold = 10.0

        result = calculate_uncertainty_threshold(uncertainties)

        assert result == expected_threshold

    def test_empty_array_raises_error(self):
        """Test that an empty array raises a ValueError."""
        uncertainties = np.array([])

        with pytest.raises(ValueError):
            calculate_uncertainty_threshold(uncertainties)

    def test_negative_values(self):
        """Test threshold calculation with negative uncertainty values (edge case)."""
        uncertainties = np.array([-2.0, -1.0, 0.0, 1.0, 2.0])
        median_val = np.median(uncertainties)  # 0.0
        expected_threshold = 0.0

        result = calculate_uncertainty_threshold(uncertainties)

        assert result == expected_threshold

    def test_large_dataset(self):
        """Test threshold calculation with a larger random dataset."""
        np.random.seed(42)
        uncertainties = np.random.rand(1000) * 100
        median_val = np.median(uncertainties)
        expected_threshold = 2 * median_val

        result = calculate_uncertainty_threshold(uncertainties)

        assert np.isclose(result, expected_threshold)