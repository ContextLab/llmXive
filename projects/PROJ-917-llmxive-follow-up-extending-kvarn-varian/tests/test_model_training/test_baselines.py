"""
Tests for the closed-form baseline predictor (T024).
"""

import pytest
import numpy as np
import sys
import os

# Ensure the code directory is in the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from model_training.baselines import (
    predict_closed_form_variance,
    evaluate_baseline_mse,
    predict_batch_variance
)


class TestClosedFormLogic:
    """Tests for the s = 1/variance logic."""

    def test_scalar_variance(self):
        """Test prediction with a scalar variance input."""
        variance = 0.04  # 1/0.04 = 25.0
        result = predict_closed_form_variance(variance)
        assert np.isclose(result, 25.0), f"Expected 25.0, got {result}"

    def test_array_mean_variance(self):
        """Test prediction with [mean, variance] input."""
        # Input: [mean=0.5, variance=0.04] -> Expected: 25.0
        moments = np.array([0.5, 0.04])
        result = predict_closed_form_variance(moments)
        assert np.isclose(result, 25.0), f"Expected 25.0, got {result}"

    def test_batch_prediction(self):
        """Test prediction with a batch of [mean, variance] rows."""
        # Row 1: var=0.04 -> 25.0
        # Row 2: var=0.01 -> 100.0
        # Row 3: var=0.25 -> 4.0
        moments = np.array([
            [0.0, 0.04],
            [0.1, 0.01],
            [0.5, 0.25]
        ])
        result = predict_batch_variance(moments)

        expected = np.array([25.0, 100.0, 4.0], dtype=np.float32)
        assert result.shape == (3,), f"Expected shape (3,), got {result.shape}"
        assert np.allclose(result, expected), f"Expected {expected}, got {result}"

    def test_zero_variance_epsilon_floor(self):
        """Test that zero variance is handled by epsilon floor."""
        # Variance = 0 should result in 1 / 1e-6 = 1,000,000
        result = predict_closed_form_variance(0.0)
        expected = 1.0 / 1e-6
        assert np.isclose(result, expected), f"Expected {expected}, got {result}"

    def test_negative_variance_epsilon_floor(self):
        """Test that negative variance is handled by epsilon floor."""
        # Negative variance should be clamped to epsilon floor
        result = predict_closed_form_variance(-0.5)
        expected = 1.0 / 1e-6
        assert np.isclose(result, expected), f"Expected {expected}, got {result}"

    def test_mse_calculation(self):
        """Test MSE evaluation function."""
        predictions = np.array([10.0, 20.0, 30.0])
        ground_truth = np.array([10.0, 25.0, 30.0])
        # Errors: [0, -5, 0] -> Squared: [0, 25, 0] -> Mean: 25/3
        expected_mse = 25.0 / 3.0
        mse = evaluate_baseline_mse(predictions, ground_truth)
        assert np.isclose(mse, expected_mse), f"Expected {expected_mse}, got {mse}"

    def test_mse_shape_mismatch(self):
        """Test that MSE raises error on shape mismatch."""
        predictions = np.array([1.0, 2.0])
        ground_truth = np.array([1.0, 2.0, 3.0])
        with pytest.raises(ValueError):
            evaluate_baseline_mse(predictions, ground_truth)
