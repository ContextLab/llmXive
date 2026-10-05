"""
Unit tests for spline-based imputation logic in the ingestion pipeline.

This module tests the spline-based imputation strategy for handling missing values
in time-series data, as mandated by the updated FR-001. It verifies that:
1. Missing values are correctly identified.
2. Spline interpolation fills gaps without altering observed values.
3. The reconstruction error (MSE) between original (with gaps filled) and
   the interpolated curve is within the tolerance (MSE <= 0.01) for smooth data.
4. The fallback to linear interpolation occurs only when spline fitting fails.
"""

import numpy as np
import pytest
from scipy.interpolate import UnivariateSpline
from scipy.signal import find_peaks

# Import the actual implementation logic from the project code.
# Note: ingestion.py is not fully implemented yet (T012-T014), so we implement
# the core imputation helper function here for testing, or import it if it exists.
# For this task, we assume the core logic resides in `code/ingestion.py` or a helper.
# Since ingestion.py is the target of future tasks, we will implement the
# `impute_with_spline` function in this file for the sake of the test,
# simulating what will eventually be in `code/ingestion.py`.
# In a real workflow, this function would be moved to `code/ingestion.py` once T013 is done.
# However, to satisfy the "extend, don't re-author" and "implement real code" constraint,
# we will create the function in `code/ingestion.py` as a minimal stub that implements
# the imputation logic, and then test it.

# Actually, the prompt says: "Extend, don't re-author. Use the provided existing API surface".
# Since `code/ingestion.py` does not exist yet (it's a future task T012),
# we must create it with the specific function needed for this test,
# or the test must define the function locally if it's purely unit-level logic
# that will be moved later.
# The prompt says: "If the task asks for an analysis, write the code that performs it".
# The task is "Unit test for spline-based imputation".
# To make the test runnable, we need the function being tested.
# We will create `code/ingestion.py` with the `impute_with_spline` function
# and the test file will import from it. This satisfies "implement real code".

import sys
import os

# Ensure code/ is in path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from code.ingestion import impute_with_spline


class TestSplineImputation:
    """Test suite for spline-based imputation."""

    def test_no_missing_values(self):
        """Test that data with no missing values remains unchanged."""
        x = np.linspace(0, 10, 50)
        y = np.sin(x)
        y_clean = y.copy()

        result = impute_with_spline(x, y)

        np.testing.assert_array_almost_equal(result, y_clean, decimal=10)

    def test_single_missing_value_interpolation(self):
        """Test imputation of a single missing value (NaN)."""
        x = np.linspace(0, 10, 50)
        y = np.sin(x)
        y_missing = y.copy()
        y_missing[25] = np.nan

        result = impute_with_spline(x, y_missing)

        # The result should be close to the original sine wave
        expected = np.sin(x)
        mse = np.mean((result - expected) ** 2)
        assert mse <= 0.01, f"MSE {mse} exceeds tolerance 0.01"
        # The observed values should be preserved (where not NaN)
        mask = ~np.isnan(y_missing)
        np.testing.assert_array_almost_equal(result[mask], y[mask], decimal=10)

    def test_multiple_consecutive_missing_values(self):
        """Test imputation of a block of missing values."""
        x = np.linspace(0, 10, 50)
        y = np.sin(x)
        y_missing = y.copy()
        # Create a gap of 5 values
        y_missing[20:25] = np.nan

        result = impute_with_spline(x, y_missing)

        expected = np.sin(x)
        mse = np.mean((result - expected) ** 2)
        assert mse <= 0.01, f"MSE {mse} exceeds tolerance 0.01"

    def test_edge_case_missing_at_start(self):
        """Test imputation when missing values are at the start."""
        x = np.linspace(0, 10, 50)
        y = np.sin(x)
        y_missing = y.copy()
        y_missing[:5] = np.nan

        result = impute_with_spline(x, y_missing)
        expected = np.sin(x)
        mse = np.mean((result - expected) ** 2)
        # Extrapolation might be slightly less accurate, but should be reasonable
        assert mse <= 0.05, f"MSE {mse} exceeds tolerance for edge case"

    def test_edge_case_missing_at_end(self):
        """Test imputation when missing values are at the end."""
        x = np.linspace(0, 10, 50)
        y = np.sin(x)
        y_missing = y.copy()
        y_missing[-5:] = np.nan

        result = impute_with_spline(x, y_missing)
        expected = np.sin(x)
        mse = np.mean((result - expected) ** 2)
        assert mse <= 0.05, f"MSE {mse} exceeds tolerance for edge case"

    def test_all_nan_raises_error(self):
        """Test that a completely empty array raises an error."""
        x = np.linspace(0, 10, 50)
        y = np.full(50, np.nan)

        with pytest.raises(ValueError):
            impute_with_spline(x, y)

    def test_fallback_to_linear_on_singular_matrix(self):
        """Test that linear interpolation is used if spline fails (e.g., too few points)."""
        # Create a case where spline might fail (very few non-NaN points)
        x = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
        y = np.array([0.0, np.nan, np.nan, np.nan, 4.0])

        # Spline with degree > 1 might fail or behave oddly with only 2 points
        # Our implementation should handle this gracefully
        result = impute_with_spline(x, y)

        # Result should be a linear interpolation between 0 and 4
        expected = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
        np.testing.assert_array_almost_equal(result, expected, decimal=1)

    def test_preserves_derivative_structure_approximation(self):
        """
        Verify that the spline imputation preserves the smoothness of the data,
        which is critical for the derivative structure required by FR-001.
        We check that the second derivative is not excessively noisy.
        """
        x = np.linspace(0, 10, 100)
        y = np.sin(x)
        y_missing = y.copy()
        y_missing[30:40] = np.nan

        result = impute_with_spline(x, y_missing)

        # Calculate second derivative numerically
        second_deriv = np.gradient(np.gradient(result, x), x)

        # The second derivative of sin(x) is -sin(x), which is bounded by [-1, 1]
        # We allow some margin for numerical error and edge effects
        assert np.max(np.abs(second_deriv)) < 2.0, "Second derivative is too large, indicating noise"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
