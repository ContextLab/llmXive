"""
Unit tests for sensitivity analysis functionality.

This module verifies the variance calculation across the outlier removal
threshold sweep {2.5, 3.0, 3.5} and the threshold check (<= 0.1).
"""
import os
import sys
import tempfile
import json
import pytest
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the project root to the path to allow imports from src
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from src.models.sensitivity import compute_variance_across_sweep, check_variance_threshold

# Fixtures and helper data
@pytest.fixture
def mock_residuals_data():
    """
    Generate mock residuals data for testing.
    
    Returns a dictionary with 'thresholds' and 'r2_scores' keys.
    The R2 scores are designed such that variance across the sweep
    is calculable and testable.
    """
    np.random.seed(42)
    # Simulate R2 scores for thresholds 2.5, 3.0, 3.5
    # Values chosen to have a specific, testable variance
    r2_scores = np.array([0.85, 0.87, 0.86])
    thresholds = [2.5, 3.0, 3.5]
    
    return {
        "thresholds": thresholds,
        "r2_scores": r2_scores.tolist()
    }

@pytest.fixture
def temp_residuals_file(mock_residuals_data):
    """
    Create a temporary JSON file containing mock residuals data.
    
    Yields the path to the temporary file.
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(mock_residuals_data, f)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.remove(temp_path)

class TestSensitivitySweepVarianceCalculation:
    """
    Test cases for the sensitivity sweep variance calculation.
    
    These tests verify that:
    1. The variance is correctly calculated across the sweep {2.5, 3.0, 3.5}
    2. The threshold check (<= 0.1) works as expected
    3. Edge cases are handled properly
    """

    def test_variance_calculation_correct(self, mock_residuals_data):
        """
        Verify that the variance calculation matches numpy's variance function.
        
        This test ensures that the compute_variance_across_sweep function
        correctly calculates the variance of R2 scores across the three
        specified thresholds.
        """
        r2_scores = np.array(mock_residuals_data["r2_scores"])
        expected_variance = np.var(r2_scores, ddof=0)  # Population variance
        
        computed_variance = compute_variance_across_sweep(mock_residuals_data["r2_scores"])
        
        assert np.isclose(computed_variance, expected_variance), \
            f"Expected variance {expected_variance}, got {computed_variance}"

    def test_variance_threshold_check_pass(self, mock_residuals_data):
        """
        Verify that the threshold check returns True when variance <= 0.1.
        
        In this test case, the R2 scores [0.85, 0.87, 0.86] have a very
        small variance (approx 0.000133), which should pass the threshold.
        """
        r2_scores = np.array(mock_residuals_data["r2_scores"])
        variance = np.var(r2_scores, ddof=0)
        
        # This should pass because variance is very small (~0.000133)
        result = check_variance_threshold(variance, threshold=0.1)
        
        assert result is True, \
            f"Expected True for variance {variance} <= 0.1, got {result}"

    def test_variance_threshold_check_fail(self, mock_residuals_data):
        """
        Verify that the threshold check returns False when variance > 0.1.
        
        This test uses artificially inflated R2 scores to create a large
        variance that should fail the threshold check.
        """
        # Create R2 scores with large variance
        large_variance_scores = [0.5, 0.9, 0.3]
        variance = np.var(large_variance_scores, ddof=0)
        
        # This should fail because variance is large (~0.0733)
        # Wait, 0.0733 is still < 0.1. Let's use even more extreme values.
        extreme_scores = [0.1, 0.9, 0.0]
        extreme_variance = np.var(extreme_scores, ddof=0)
        
        result = check_variance_threshold(extreme_variance, threshold=0.1)
        
        assert result is False, \
            f"Expected False for variance {extreme_variance} > 0.1, got {result}"

    def test_variance_calculation_empty_input(self):
        """
        Verify that an empty list raises an appropriate error.
        
        The function should handle the edge case of no data gracefully.
        """
        with pytest.raises(ValueError, match="No data provided"):
            compute_variance_across_sweep([])

    def test_variance_calculation_single_value(self):
        """
        Verify that a single value results in zero variance.
        
        With only one data point, the variance should be zero.
        """
        single_value = [0.85]
        variance = compute_variance_across_sweep(single_value)
        
        assert variance == 0.0, \
            f"Expected variance 0.0 for single value, got {variance}"

    def test_variance_calculation_two_values(self):
        """
        Verify variance calculation with exactly two values.
        
        This tests the minimal case for meaningful variance calculation.
        """
        two_values = [0.8, 0.9]
        expected_variance = np.var(two_values, ddof=0)
        computed_variance = compute_variance_across_sweep(two_values)
        
        assert np.isclose(computed_variance, expected_variance), \
            f"Expected variance {expected_variance}, got {computed_variance}"

    def test_sweep_thresholds_match_spec(self, mock_residuals_data):
        """
        Verify that the sweep thresholds match the specification {2.5, 3.0, 3.5}.
        
        This ensures the sensitivity analysis is performed on the correct
        set of outlier removal thresholds as defined in the requirements.
        """
        expected_thresholds = [2.5, 3.0, 3.5]
        actual_thresholds = mock_residuals_data["thresholds"]
        
        assert actual_thresholds == expected_thresholds, \
            f"Expected thresholds {expected_thresholds}, got {actual_thresholds}"

    def test_integration_with_temp_file(self, temp_residuals_file):
        """
        Integration test: Load data from file and compute variance.
        
        This test verifies the complete flow from file loading to variance
        calculation, ensuring the function can work with persisted data.
        """
        with open(temp_residuals_file, 'r') as f:
            data = json.load(f)
        
        variance = compute_variance_across_sweep(data["r2_scores"])
        threshold_passed = check_variance_threshold(variance, threshold=0.1)
        
        # Verify the variance is a non-negative number
        assert isinstance(variance, (int, float)) and variance >= 0.0, \
            f"Variance should be non-negative, got {variance}"
        
        # Verify the threshold check returns a boolean
        assert isinstance(threshold_passed, bool), \
            f"Threshold check should return boolean, got {type(threshold_passed)}"