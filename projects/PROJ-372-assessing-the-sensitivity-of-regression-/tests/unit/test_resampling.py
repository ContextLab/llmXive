"""
Unit tests for singularity detection in the resampling engine.

This module verifies that the resampling logic correctly identifies
singular matrices (infinite condition number) and raises LinAlgError
instead of crashing or producing NaN coefficients.
"""

import numpy as np
import pytest
import statsmodels.api as sm
from numpy.linalg import LinAlgError

from src.resampling.engine import _fit_ols_safely


class TestSingularityDetection:
    """Tests for detecting and handling singular matrix errors."""

    def test_singular_matrix_raises_linalg_error(self):
        """
        Verify that fitting OLS on data with a condition number > 1e15
        raises a LinAlgError.

        We construct a fixed 2D array where one column is a linear
        combination of another, creating a singular design matrix.
        """
        # Create a fixed dataset with perfect multicollinearity
        # Shape: (n_samples, n_features) = (100, 3)
        # Feature 0 and Feature 1 are identical -> Singular matrix
        np.random.seed(42)
        n_samples = 100
        n_features = 3

        X = np.random.randn(n_samples, 2)
        X = np.column_stack([X, X[:, 0]])  # 3rd column = 1st column

        # Add intercept (statsmodels doesn't add it by default)
        X_with_intercept = sm.add_constant(X)

        # Check condition number (should be very high/infinite)
        try:
            cond_num = np.linalg.cond(X_with_intercept)
            assert cond_num > 1e15 or np.isinf(cond_num), (
                f"Expected condition number > 1e15, got {cond_num}"
            )
        except LinAlgError:
            # If cond() itself fails, that's also evidence of singularity
            pass

        y = np.random.randn(n_samples)

        # The function should raise LinAlgError for singular matrices
        with pytest.raises(LinAlgError) as exc_info:
            _fit_ols_safely(X_with_intercept, y)

        # Verify the error message mentions singular matrix or similar
        assert "singular" in str(exc_info.value).lower() or "rank" in str(exc_info.value).lower(), (
            f"Expected 'singular' or 'rank' in error message, got: {exc_info.value}"
        )

    def test_near_singular_matrix_raises_linalg_error(self):
        """
        Verify that fitting OLS on data with near-singularity
        (condition number > 1e15) raises a LinAlgError.
        """
        # Create data with near-perfect multicollinearity
        np.random.seed(123)
        n_samples = 50
        
        # Create two nearly identical columns
        X1 = np.random.randn(n_samples)
        X2 = X1 + 1e-16 * np.random.randn(n_samples)  # Tiny noise
        
        X = np.column_stack([X1, X2])
        X_with_intercept = sm.add_constant(X)
        
        # Verify condition number is extremely high
        cond_num = np.linalg.cond(X_with_intercept)
        assert cond_num > 1e15, (
            f"Expected condition number > 1e15 for near-singular test, got {cond_num}"
        )
        
        y = np.random.randn(n_samples)
        
        # Should raise LinAlgError
        with pytest.raises(LinAlgError):
            _fit_ols_safely(X_with_intercept, y)

    def test_well_conditioned_matrix_fits_successfully(self):
        """
        Verify that well-conditioned data (low condition number)
        fits successfully without raising an error.
        """
        np.random.seed(456)
        n_samples = 100
        n_features = 3
        
        # Generate well-conditioned random data
        X = np.random.randn(n_samples, n_features)
        X_with_intercept = sm.add_constant(X)
        
        # Verify condition number is reasonable
        cond_num = np.linalg.cond(X_with_intercept)
        assert cond_num < 1000, (
            f"Expected well-conditioned matrix (cond < 1000), got {cond_num}"
        )
        
        y = np.random.randn(n_samples)
        
        # Should fit successfully
        result = _fit_ols_safely(X_with_intercept, y)
        
        # Verify we got a valid result
        assert result is not None
        assert hasattr(result, 'params')
        assert len(result.params) == n_features + 1  # +1 for intercept

    def test_exact_two_dimensional_shape_singular(self):
        """
        Specific test case: fixed 2D shape (10, 2) with condition number > 1e15.
        Ensures the singularity detection works for small, fixed-size inputs.
        """
        # Fixed 2D shape: (10 samples, 2 features)
        # Create perfect multicollinearity
        X = np.array([
            [1.0, 1.0],
            [2.0, 2.0],
            [3.0, 3.0],
            [4.0, 4.0],
            [5.0, 5.0],
            [6.0, 6.0],
            [7.0, 7.0],
            [8.0, 8.0],
            [9.0, 9.0],
            [10.0, 10.0],
        ], dtype=np.float64)
        
        X_with_intercept = sm.add_constant(X)
        
        # Verify condition number
        cond_num = np.linalg.cond(X_with_intercept)
        assert cond_num > 1e15 or np.isinf(cond_num), (
            f"Expected condition number > 1e15 for 2D singular test, got {cond_num}"
        )
        
        y = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0])
        
        # Should raise LinAlgError
        with pytest.raises(LinAlgError):
            _fit_ols_safely(X_with_intercept, y)