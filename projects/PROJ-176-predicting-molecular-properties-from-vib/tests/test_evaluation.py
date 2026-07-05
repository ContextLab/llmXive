"""
Unit tests for metrics calculation in code/evaluation/metrics.py.
Verifies MAE and R² formulas against known analytical results.
"""
import pytest
import numpy as np
import sys
from pathlib import Path

# Ensure project root is in path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from evaluation.metrics import calculate_mae, calculate_r2


class TestMAE:
    """Tests for Mean Absolute Error calculation."""

    def test_mae_perfect_prediction(self):
        """MAE should be 0.0 for perfect predictions."""
        y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y_pred = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        mae = calculate_mae(y_true, y_pred)
        assert np.isclose(mae, 0.0), f"Expected 0.0, got {mae}"

    def test_mae_constant_error(self):
        """MAE should equal the constant error value."""
        y_true = np.array([10.0, 20.0, 30.0])
        y_pred = np.array([12.0, 22.0, 32.0])  # Error is always +2.0
        mae = calculate_mae(y_true, y_pred)
        assert np.isclose(mae, 2.0), f"Expected 2.0, got {mae}"

    def test_mae_mixed_errors(self):
        """MAE for mixed positive and negative errors."""
        # Errors: +1, -2, +3, -4 -> Absolute: 1, 2, 3, 4 -> Mean: 2.5
        y_true = np.array([1.0, 2.0, 3.0, 4.0])
        y_pred = np.array([2.0, 0.0, 6.0, 0.0])
        mae = calculate_mae(y_true, y_pred)
        expected = (1 + 2 + 3 + 4) / 4.0
        assert np.isclose(mae, expected), f"Expected {expected}, got {mae}"

    def test_mae_single_value(self):
        """MAE for a single data point."""
        y_true = np.array([5.0])
        y_pred = np.array([8.0])
        mae = calculate_mae(y_true, y_pred)
        assert np.isclose(mae, 3.0), f"Expected 3.0, got {mae}"


class TestR2:
    """Tests for R-squared (Coefficient of Determination) calculation."""

    def test_r2_perfect_prediction(self):
        """R² should be 1.0 for perfect predictions."""
        y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y_pred = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        r2 = calculate_r2(y_true, y_pred)
        assert np.isclose(r2, 1.0), f"Expected 1.0, got {r2}"

    def test_r2_mean_prediction(self):
        """R² should be 0.0 if predictions are always the mean of y_true."""
        y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        mean_val = np.mean(y_true)
        y_pred = np.array([mean_val] * len(y_true))
        r2 = calculate_r2(y_true, y_pred)
        assert np.isclose(r2, 0.0), f"Expected 0.0, got {r2}"

    def test_r2_negative(self):
        """R² can be negative if predictions are arbitrarily bad."""
        # y_true: [1, 2, 3], mean = 2. SS_tot = (1-2)^2 + (2-2)^2 + (3-2)^2 = 2
        # y_pred: [10, 10, 10], SS_res = (1-10)^2 + (2-10)^2 + (3-10)^2 = 81 + 64 + 49 = 194
        # R² = 1 - (194/2) = 1 - 97 = -96
        y_true = np.array([1.0, 2.0, 3.0])
        y_pred = np.array([10.0, 10.0, 10.0])
        r2 = calculate_r2(y_true, y_pred)
        expected = 1.0 - (194.0 / 2.0)
        assert np.isclose(r2, expected), f"Expected {expected}, got {r2}"

    def test_r2_mixed_values(self):
        """R² for a specific mixed case."""
        # y_true = [2, 4, 6], mean = 4
        # SS_tot = (2-4)^2 + (4-4)^2 + (6-4)^2 = 4 + 0 + 4 = 8
        # y_pred = [3, 4, 5]
        # SS_res = (2-3)^2 + (4-4)^2 + (6-5)^2 = 1 + 0 + 1 = 2
        # R² = 1 - (2/8) = 0.75
        y_true = np.array([2.0, 4.0, 6.0])
        y_pred = np.array([3.0, 4.0, 5.0])
        r2 = calculate_r2(y_true, y_pred)
        assert np.isclose(r2, 0.75), f"Expected 0.75, got {r2}"

    def test_r2_single_value_edge_case(self):
        """R² for a single value (SS_tot=0) should handle division by zero gracefully or raise."""
        # Note: Standard R2 definition is undefined for single value if variance is 0.
        # Our implementation should handle this.
        y_true = np.array([5.0])
        y_pred = np.array([5.0])
        # If implementation returns 1.0 for perfect single match or 0.0 or raises,
        # we just ensure it doesn't crash with a generic error.
        # Assuming standard behavior: 1.0 if perfect, else undefined.
        # Let's test a case where it's perfect.
        try:
            r2 = calculate_r2(y_true, y_pred)
            # If it runs, it should be 1.0 for perfect match
            assert np.isclose(r2, 1.0) or np.isnan(r2)
        except ZeroDivisionError:
            # If the implementation explicitly raises for single point, that's also acceptable
            pass