"""
Unit tests for UQ metrics calculations in code/uq/metrics.py
"""

import pytest
import numpy as np
import pandas as pd
from code.uq.metrics import (
    calculate_ece,
    calculate_interval_score,
    calculate_sharpness,
    compute_uq_metrics,
    evaluate_all_methods
)


class TestECE:
    def test_ece_perfect_calibration(self):
        """Test ECE with perfectly calibrated predictions."""
        # Perfect calibration: 90% of points within 90% CI
        n_samples = 1000
        predictions = np.random.normal(0, 1, n_samples)
        uncertainties = np.ones(n_samples)  # Constant uncertainty

        # Create actuals such that exactly 90% are within 1.645 std
        from scipy.stats import norm
        z_threshold = norm.ppf(0.95)

        # Generate actuals with the desired coverage
        actuals = np.zeros(n_samples)
        for i in range(n_samples):
            if i < int(0.9 * n_samples):
                actuals[i] = predictions[i] + np.random.uniform(-z_threshold, z_threshold) * uncertainties[i]
            else:
                actuals[i] = predictions[i] + np.random.uniform(z_threshold, z_threshold + 2) * uncertainties[i]

        ece = calculate_ece(predictions, uncertainties, actuals, n_bins=10, confidence_level=0.9)

        # ECE should be relatively low for well-calibrated predictions
        # Note: Due to binning and randomness, it won't be exactly 0
        assert ece >= 0
        assert ece < 0.5  # Reasonable upper bound

    def test_ece_mis_calibration(self):
        """Test ECE with mis-calibrated predictions."""
        predictions = np.random.normal(0, 1, 1000)
        uncertainties = np.ones(1000)

        # Create actuals with very poor coverage (e.g., only 50% within 90% CI)
        actuals = predictions + np.random.normal(0, 3, 1000)  # High variance

        ece = calculate_ece(predictions, uncertainties, actuals, n_bins=10, confidence_level=0.9)

        # ECE should be higher for mis-calibrated predictions
        assert ece > 0

    def test_ece_mismatched_lengths(self):
        """Test that ECE raises error for mismatched input lengths."""
        with pytest.raises(ValueError):
            calculate_ece(
                np.array([1, 2, 3]),
                np.array([1, 2]),
                np.array([1, 2, 3])
            )


class TestIntervalScore:
    def test_interval_score_perfect_coverage(self):
        """Test Interval Score with perfect coverage and narrow intervals."""
        predictions = np.array([0.0, 0.0, 0.0, 0.0, 0.0])
        lower_bounds = np.array([-1.0, -1.0, -1.0, -1.0, -1.0])
        upper_bounds = np.array([1.0, 1.0, 1.0, 1.0, 1.0])
        actuals = np.array([0.0, 0.0, 0.0, 0.0, 0.0])

        score = calculate_interval_score(predictions, lower_bounds, upper_bounds, actuals, alpha=0.1)

        # Perfect coverage: score should equal the width
        expected_width = 2.0
        assert np.isclose(score, expected_width)

    def test_interval_score_missing_lower(self):
        """Test Interval Score when actual is below lower bound."""
        predictions = np.array([0.0])
        lower_bounds = np.array([1.0])
        upper_bounds = np.array([3.0])
        actuals = np.array([0.0])  # Below lower bound

        score = calculate_interval_score(predictions, lower_bounds, upper_bounds, actuals, alpha=0.1)

        # Width = 2.0, Penalty = 2/0.1 * (1.0 - 0.0) = 20.0
        # Total = 22.0
        expected = 2.0 + 20.0
        assert np.isclose(score, expected)

    def test_interval_score_missing_upper(self):
        """Test Interval Score when actual is above upper bound."""
        predictions = np.array([0.0])
        lower_bounds = np.array([-3.0])
        upper_bounds = np.array([-1.0])
        actuals = np.array([0.0])  # Above upper bound

        score = calculate_interval_score(predictions, lower_bounds, upper_bounds, actuals, alpha=0.1)

        # Width = 2.0, Penalty = 2/0.1 * (0.0 - (-1.0)) = 20.0
        # Total = 22.0
        expected = 2.0 + 20.0
        assert np.isclose(score, expected)

    def test_interval_score_mismatched_lengths(self):
        """Test that Interval Score raises error for mismatched input lengths."""
        with pytest.raises(ValueError):
            calculate_interval_score(
                np.array([1, 2, 3]),
                np.array([1, 2]),
                np.array([1, 2, 3]),
                np.array([1, 2, 3])
            )


class TestSharpness:
    def test_sharpness_std(self):
        """Test Sharpness calculation using standard deviation."""
        uncertainties = np.array([1.0, 2.0, 3.0, 4.0])
        sharpness = calculate_sharpness(uncertainties, method="std")
        expected = np.mean(uncertainties)
        assert np.isclose(sharpness, expected)

    def test_sharpness_variance(self):
        """Test Sharpness calculation using variance."""
        uncertainties = np.array([1.0, 2.0, 3.0, 4.0])
        sharpness = calculate_sharpness(uncertainties, method="variance")
        expected = np.mean(uncertainties ** 2)
        assert np.isclose(sharpness, expected)

    def test_sharpness_invalid_method(self):
        """Test that Sharpness raises error for invalid method."""
        with pytest.raises(ValueError):
            calculate_sharpness(np.array([1.0, 2.0]), method="invalid")


class TestComputeUQMetrics:
    def test_compute_metrics_basic(self):
        """Test basic metric computation."""
        df = pd.DataFrame({
            'prediction': [1.0, 2.0, 3.0],
            'variance': [0.1, 0.2, 0.3],
            'actual': [1.1, 1.9, 3.2]
        })

        metrics = compute_uq_metrics(df, method="test")

        assert "ece" in metrics
        assert "interval_score" in metrics
        assert "sharpness" in metrics
        assert metrics["method"] == "test"
        assert metrics["ece"] is not None
        assert metrics["sharpness"] is not None

    def test_compute_metrics_with_bounds(self):
        """Test metric computation with pre-computed bounds."""
        df = pd.DataFrame({
            'prediction': [1.0, 2.0, 3.0],
            'variance': [0.1, 0.2, 0.3],
            'lower_90': [0.5, 1.5, 2.5],
            'upper_90': [1.5, 2.5, 3.5],
            'actual': [1.1, 1.9, 3.2]
        })

        metrics = compute_uq_metrics(df, method="test")

        assert metrics["interval_score"] is not None


class TestEvaluateAllMethods:
    def test_evaluate_all_methods(self):
        """Test evaluation of multiple methods."""
        df = pd.DataFrame({
            'prediction': [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
            'variance': [0.1, 0.2, 0.3, 0.1, 0.2, 0.3],
            'method': ['method1', 'method1', 'method1', 'method2', 'method2', 'method2'],
            'actual': [1.1, 1.9, 3.2, 4.1, 4.9, 6.2]
        })

        results = evaluate_all_methods(df)

        assert len(results) == 2
        assert set(results['method']) == {'method1', 'method2'}
        assert all(results['ece'].notna())
        assert all(results['sharpness'].notna())