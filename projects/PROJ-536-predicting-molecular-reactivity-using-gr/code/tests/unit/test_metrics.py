"""
Unit tests for metric calculators in src.utils.metrics.
"""
import pytest
import numpy as np

from src.utils.metrics import calculate_mae, calculate_rmse, calculate_r2, calculate_all_metrics


class TestCalculateMAE:
    def test_calculate_mae_basic(self):
        """Test basic MAE calculation."""
        y_true = [3.0, -0.5, 2.0, 7.0]
        y_pred = [2.5, 0.0, 2.0, 8.0]
        # Errors: 0.5, 0.5, 0.0, 1.0 -> Mean = 2.0 / 4 = 0.5
        expected = 0.5
        assert calculate_mae(y_true, y_pred) == pytest.approx(expected)

    def test_calculate_mae_numpy(self):
        """Test MAE with numpy arrays."""
        y_true = np.array([1.0, 2.0, 3.0])
        y_pred = np.array([1.0, 2.0, 3.0])
        assert calculate_mae(y_true, y_pred) == pytest.approx(0.0)

    def test_mae_empty_input(self):
        """Test that empty input raises ValueError."""
        with pytest.raises(ValueError, match="empty"):
            calculate_mae([], [])

    def test_mae_mismatched_lengths(self):
        """Test that mismatched lengths raise ValueError."""
        with pytest.raises(ValueError, match="lengths must match"):
            calculate_mae([1, 2], [1])


class TestCalculateRMSE:
    def test_calculate_rmse_basic(self):
        """Test basic RMSE calculation."""
        y_true = [3.0, -0.5, 2.0, 7.0]
        y_pred = [2.5, 0.0, 2.0, 8.0]
        # Squared errors: 0.25, 0.25, 0.0, 1.0 -> Mean = 1.5 / 4 = 0.375
        # RMSE = sqrt(0.375) approx 0.61237
        expected = np.sqrt(0.375)
        assert calculate_rmse(y_true, y_pred) == pytest.approx(expected)

    def test_rmse_perfect_prediction(self):
        """Test RMSE is 0 for perfect predictions."""
        y_true = [1.0, 2.0, 3.0]
        y_pred = [1.0, 2.0, 3.0]
        assert calculate_rmse(y_true, y_pred) == pytest.approx(0.0)


class TestCalculateR2:
    def test_calculate_r2_perfect(self):
        """Test R² is 1.0 for perfect predictions."""
        y_true = [1.0, 2.0, 3.0, 4.0]
        y_pred = [1.0, 2.0, 3.0, 4.0]
        assert calculate_r2(y_true, y_pred) == pytest.approx(1.0)

    def test_calculate_r2_worse_than_mean(self):
        """Test R² can be negative if predictions are worse than mean."""
        y_true = [1.0, 2.0, 3.0]
        y_pred = [3.0, 2.0, 1.0] # Mean of y_true is 2.0.
        # SS_res = (1-3)^2 + (2-2)^2 + (3-1)^2 = 4 + 0 + 4 = 8
        # SS_tot = (1-2)^2 + (2-2)^2 + (3-2)^2 = 1 + 0 + 1 = 2
        # R2 = 1 - (8/2) = -3.0
        assert calculate_r2(y_true, y_pred) == pytest.approx(-3.0)

    def test_r2_zero_variance(self):
        """Test R² raises error if y_true has zero variance and predictions are not perfect."""
        y_true = [2.0, 2.0, 2.0]
        y_pred = [2.0, 2.0, 2.0] # Perfect prediction despite zero variance
        assert calculate_r2(y_true, y_pred) == pytest.approx(1.0)

        y_pred_bad = [1.0, 2.0, 3.0]
        with pytest.raises(ValueError, match="zero variance"):
            calculate_r2(y_true, y_pred_bad)


class TestCalculateAllMetrics:
    def test_calculate_all_metrics(self):
        """Test that calculate_all_metrics returns correct dictionary."""
        y_true = [1.0, 2.0, 3.0, 4.0]
        y_pred = [1.1, 2.1, 2.9, 4.1]
        
        results = calculate_all_metrics(y_true, y_pred)
        
        assert "mae" in results
        assert "rmse" in results
        assert "r2" in results
        
        assert isinstance(results["mae"], float)
        assert isinstance(results["rmse"], float)
        assert isinstance(results["r2"], float)
        
        # Verify consistency with individual functions
        assert results["mae"] == pytest.approx(calculate_mae(y_true, y_pred))
        assert results["rmse"] == pytest.approx(calculate_rmse(y_true, y_pred))
        assert results["r2"] == pytest.approx(calculate_r2(y_true, y_pred))