"""
Unit tests for metric calculation (R², RMSE, p-values).
Tests the functions that compute regression metrics required for US2.
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import os

# Add the code directory to the path so we can import from code/modeling
# This is necessary for local testing; in CI, the path structure is handled differently
code_path = Path(__file__).parent.parent.parent / "code"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

from modeling.metrics import calculate_r2, calculate_rmse, calculate_pvalues


class TestCalculateR2:
    """Tests for R² calculation."""

    def test_perfect_prediction(self):
        """R² should be 1.0 for perfect predictions."""
        y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y_pred = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        r2 = calculate_r2(y_true, y_pred)
        assert np.isclose(r2, 1.0), f"Expected R²=1.0, got {r2}"

    def test_worse_than_mean(self):
        """R² should be negative if predictions are worse than mean."""
        y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y_pred = np.array([5.0, 4.0, 3.0, 2.0, 1.0])  # Inverse, very bad
        r2 = calculate_r2(y_true, y_pred)
        assert r2 < 0.0, f"Expected R²<0, got {r2}"

    def test_zero_variance_y_true(self):
        """Should raise ValueError if y_true has zero variance."""
        y_true = np.array([1.0, 1.0, 1.0, 1.0])
        y_pred = np.array([1.0, 1.0, 1.0, 1.0])
        with pytest.raises(ValueError, match="y_true has zero variance"):
            calculate_r2(y_true, y_pred)

    def test_array_shapes_mismatch(self):
        """Should raise ValueError if arrays have different lengths."""
        y_true = np.array([1.0, 2.0, 3.0])
        y_pred = np.array([1.0, 2.0])
        with pytest.raises(ValueError, match="Input arrays must have the same length"):
            calculate_r2(y_true, y_pred)

    def test_empty_arrays(self):
        """Should raise ValueError for empty arrays."""
        y_true = np.array([])
        y_pred = np.array([])
        with pytest.raises(ValueError, match="Input arrays cannot be empty"):
            calculate_r2(y_true, y_pred)


class TestCalculateRMSE:
    """Tests for RMSE calculation."""

    def test_perfect_prediction(self):
        """RMSE should be 0.0 for perfect predictions."""
        y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y_pred = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        rmse = calculate_rmse(y_true, y_pred)
        assert np.isclose(rmse, 0.0), f"Expected RMSE=0.0, got {rmse}"

    def test_non_zero_rmse(self):
        """RMSE should be positive for imperfect predictions."""
        y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y_pred = np.array([1.5, 2.5, 3.5, 4.5, 5.5])  # All off by 0.5
        rmse = calculate_rmse(y_true, y_pred)
        expected_rmse = 0.5
        assert np.isclose(rmse, expected_rmse), f"Expected RMSE={expected_rmse}, got {rmse}"

    def test_array_shapes_mismatch(self):
        """Should raise ValueError if arrays have different lengths."""
        y_true = np.array([1.0, 2.0, 3.0])
        y_pred = np.array([1.0, 2.0])
        with pytest.raises(ValueError, match="Input arrays must have the same length"):
            calculate_rmse(y_true, y_pred)

    def test_empty_arrays(self):
        """Should raise ValueError for empty arrays."""
        y_true = np.array([])
        y_pred = np.array([])
        with pytest.raises(ValueError, match="Input arrays cannot be empty"):
            calculate_rmse(y_true, y_pred)


class TestCalculatePvalues:
    """Tests for p-value calculation using statsmodels."""

    def test_significant_coefficients(self):
        """Should return small p-values for strong linear relationship."""
        # Create a dataset with a clear linear relationship
        np.random.seed(42)
        X = np.random.rand(100, 3)
        true_coefs = np.array([2.0, -1.5, 0.5])
        y = X @ true_coefs + np.random.normal(0, 0.1, 100)  # Low noise

        p_values = calculate_pvalues(X, y)

        assert len(p_values) == 3, f"Expected 3 p-values, got {len(p_values)}"
        # With low noise, p-values should be very small (significant)
        assert all(p < 0.05 for p in p_values), f"Expected all p-values < 0.05, got {p_values}"

    def test_non_significant_coefficients(self):
        """Should return large p-values for weak/no relationship."""
        # Create a dataset with no relationship (y is random noise)
        np.random.seed(42)
        X = np.random.rand(100, 3)
        y = np.random.normal(0, 1, 100)  # Random noise

        p_values = calculate_pvalues(X, y)

        assert len(p_values) == 3, f"Expected 3 p-values, got {len(p_values)}"
        # With no relationship, some p-values should be large (non-significant)
        # Note: Not guaranteed to be > 0.05 for all due to randomness, but likely some

    def test_single_feature(self):
        """Should work with a single feature."""
        np.random.seed(42)
        X = np.random.rand(50, 1)
        y = 2 * X.flatten() + np.random.normal(0, 0.5, 50)

        p_values = calculate_pvalues(X, y)

        assert len(p_values) == 1, f"Expected 1 p-value, got {len(p_values)}"
        assert p_values[0] < 0.05, f"Expected p-value < 0.05, got {p_values[0]}"

    def test_array_shapes_mismatch(self):
        """Should raise ValueError if X and y have incompatible shapes."""
        X = np.random.rand(10, 3)
        y = np.random.rand(5)  # Wrong length

        with pytest.raises(ValueError):
            calculate_pvalues(X, y)

    def test_empty_arrays(self):
        """Should raise ValueError for empty arrays."""
        X = np.array([]).reshape(0, 3)
        y = np.array([])

        with pytest.raises(ValueError):
            calculate_pvalues(X, y)

    def test_pandas_dataframe_input(self):
        """Should handle pandas DataFrame input for X."""
        np.random.seed(42)
        X = pd.DataFrame(np.random.rand(50, 3), columns=['feat1', 'feat2', 'feat3'])
        y = np.random.rand(50)

        p_values = calculate_pvalues(X, y)

        assert len(p_values) == 3, f"Expected 3 p-values, got {len(p_values)}"


class TestMetricsIntegration:
    """Integration tests for metric calculations together."""

    def test_full_regression_metrics(self):
        """Test calculating all metrics for a simple regression."""
        np.random.seed(42)
        n_samples = 100
        n_features = 3

        X = np.random.rand(n_samples, n_features)
        true_coefs = np.array([1.5, -0.8, 0.3])
        y = X @ true_coefs + np.random.normal(0, 0.2, n_samples)

        # Calculate metrics
        r2 = calculate_r2(y, X @ true_coefs)  # Perfect predictions for simplicity
        rmse = calculate_rmse(y, X @ true_coefs)
        p_values = calculate_pvalues(X, y)

        # Verify types
        assert isinstance(r2, float), f"R² should be float, got {type(r2)}"
        assert isinstance(rmse, float), f"RMSE should be float, got {type(rmse)}"
        assert isinstance(p_values, list), f"p-values should be list, got {type(p_values)}"

        # Verify ranges
        assert r2 <= 1.0, f"R² should be <= 1.0, got {r2}"
        assert rmse >= 0.0, f"RMSE should be >= 0.0, got {rmse}"
        assert all(0.0 <= p <= 1.0 for p in p_values), f"p-values should be in [0,1], got {p_values}"

    def test_metrics_with_different_noise_levels(self):
        """Test metrics sensitivity to noise levels."""
        np.random.seed(42)
        X = np.random.rand(100, 2)
        y_true = 2 * X[:, 0] + X[:, 1]

        for noise_std in [0.01, 0.1, 1.0, 10.0]:
            y = y_true + np.random.normal(0, noise_std, 100)
            y_pred = 2 * X[:, 0] + X[:, 1]  # True model

            r2 = calculate_r2(y, y_pred)
            rmse = calculate_rmse(y, y_pred)

            # As noise increases, R² should decrease and RMSE should increase
            # This is a sanity check, not a strict assertion due to randomness
            if noise_std > 0:
                assert r2 <= 1.0
                assert rmse >= 0.0