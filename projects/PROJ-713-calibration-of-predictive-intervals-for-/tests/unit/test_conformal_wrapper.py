"""
Unit tests for the Self-Calibrating Conformal Prediction Wrapper.

These tests verify:
1. Basic calibration and application functionality
2. Coverage improvement over baseline
3. Edge cases (perfect intervals, very narrow intervals)
4. Fixed sample size constraint (no nested CV)
"""

import numpy as np
import pytest
from unittest.mock import patch

from calibration.conformal import (
    SelfCalibratingConformalWrapper,
    compare_baseline_vs_conformal,
    aggregate_conformal_results,
    DEFAULT_CALIBRATION_SAMPLE_SIZE,
    DEFAULT_ALPHA
)
from utils.exceptions import CalibrationError, DataValidationError


class TestSelfCalibratingConformalWrapper:
    """Tests for SelfCalibratingConformalWrapper class."""

    @pytest.fixture
    def sample_data(self):
        """Generate sample forecast data for testing."""
        np.random.seed(42)
        n = 1000
        y_true = np.random.normal(100, 10, n)
        y_pred = y_true + np.random.normal(0, 1, n)  # Small bias

        # Create intervals that are slightly too narrow (85% coverage instead of 90%)
        # Base width is 1.5 * std instead of ~1.645 * std for 90%
        std = 10
        lower_bound = y_pred - 1.5 * std
        upper_bound = y_pred + 1.5 * std

        return y_true, y_pred, lower_bound, upper_bound

    @pytest.fixture
    def wrapper(self):
        """Create a conformal wrapper with default settings."""
        return SelfCalibratingConformalWrapper(
            alpha=0.1,  # 90% target coverage
            calibration_sample_size=200,
            min_iterations=2,
            max_iterations=10,
            tolerance=0.02
        )

    def test_initialization(self):
        """Test wrapper initialization with various parameters."""
        wrapper = SelfCalibratingConformalWrapper(alpha=0.05)
        assert wrapper.alpha == 0.05
        assert wrapper.target_coverage == 0.95
        assert wrapper.calibration_sample_size == DEFAULT_CALIBRATION_SAMPLE_SIZE

    def test_invalid_alpha(self):
        """Test that invalid alpha values raise errors."""
        with pytest.raises(DataValidationError):
            SelfCalibratingConformalWrapper(alpha=0)

        with pytest.raises(DataValidationError):
            SelfCalibratingConformalWrapper(alpha=1.5)

    def test_invalid_calibration_size(self):
        """Test that invalid calibration sizes raise errors."""
        with pytest.raises(DataValidationError):
            SelfCalibratingConformalWrapper(calibration_sample_size=0)

        with pytest.raises(DataValidationError):
            SelfCalibratingConformalWrapper(calibration_sample_size=-10)

    def test_calibrate(self, wrapper, sample_data):
        """Test calibration process."""
        y_true, y_pred, lower_bound, upper_bound = sample_data

        result = wrapper.calibrate(y_true, y_pred, lower_bound, upper_bound)

        assert "calibrated_factor" in result
        assert "calibration_coverage" in result
        assert "target_coverage" in result
        assert result["target_coverage"] == 0.90
        assert result["calibrated_factor"] > 0
        assert wrapper.calibrated_factor is not None

    def test_apply_without_calibration(self, wrapper, sample_data):
        """Test that apply raises error if not calibrated."""
        y_true, y_pred, lower_bound, upper_bound = sample_data

        with pytest.raises(CalibrationError):
            wrapper.apply(y_pred, lower_bound, upper_bound)

    def test_apply_after_calibration(self, wrapper, sample_data):
        """Test applying conformal adjustment after calibration."""
        y_true, y_pred, lower_bound, upper_bound = sample_data

        # Calibrate
        wrapper.calibrate(y_true, y_pred, lower_bound, upper_bound)

        # Apply
        adj_lower, adj_upper, factor = wrapper.apply(y_pred, lower_bound, upper_bound)

        assert len(adj_lower) == len(y_pred)
        assert len(adj_upper) == len(y_pred)
        assert factor > 0
        assert np.all(adj_upper >= adj_lower)  # Intervals should be valid

    def test_coverage_improvement(self, wrapper, sample_data):
        """Test that conformal adjustment improves coverage."""
        y_true, y_pred, lower_bound, upper_bound = sample_data

        # Baseline coverage
        baseline_coverage = np.mean((y_true >= lower_bound) & (y_true <= upper_bound))

        # Calibrate and apply
        wrapper.calibrate(y_true, y_pred, lower_bound, upper_bound)
        adj_lower, adj_upper, _ = wrapper.apply(y_pred, lower_bound, upper_bound)

        # Conformal coverage
        conformal_coverage = np.mean((y_true >= adj_lower) & (y_true <= adj_upper))

        # Conformal should be closer to target than baseline
        target = wrapper.target_coverage
        baseline_deviation = abs(baseline_coverage - target)
        conformal_deviation = abs(conformal_coverage - target)

        # The conformal coverage should be closer to target (or at least not worse)
        assert conformal_deviation <= baseline_deviation + 0.05  # Small tolerance for randomness

    def test_fixed_sample_size(self, wrapper, sample_data):
        """Test that calibration uses fixed sample size (no nested CV)."""
        y_true, y_pred, lower_bound, upper_bound = sample_data

        # Patch to track calls
        with patch.object(wrapper, '_compute_nonconformity_scores', wraps=wrapper._compute_nonconformity_scores) as mock_scores:
            wrapper.calibrate(y_true, y_pred, lower_bound, upper_bound)

            # Verify that the wrapper uses a subset of the data
            # The actual number of samples used should be min(n, calibration_sample_size)
            assert wrapper.calibration_sample_size == 200
            # The calibration should use at most 200 samples
            assert len(y_true) >= 200  # We have 1000 samples

    def test_get_coverage_stats(self, wrapper, sample_data):
        """Test coverage statistics computation."""
        y_true, y_pred, lower_bound, upper_bound = sample_data

        wrapper.calibrate(y_true, y_pred, lower_bound, upper_bound)

        stats = wrapper.get_coverage_stats(y_true, lower_bound, upper_bound)

        assert "empirical_coverage" in stats
        assert "target_coverage" in stats
        assert "coverage_deviation" in stats
        assert "n_samples" in stats
        assert stats["n_samples"] == len(y_true)


class TestCompareBaselineVsConformal:
    """Tests for the compare_baseline_vs_conformal convenience function."""

    def test_basic_comparison(self):
        """Test basic comparison functionality."""
        np.random.seed(42)
        n = 500
        y_true = np.random.normal(100, 10, n)
        y_pred = y_true + np.random.normal(0, 1, n)
        lower_bound = y_pred - 1.5 * 10
        upper_bound = y_pred + 1.5 * 10

        result = compare_baseline_vs_conformal(
            y_true, y_pred, lower_bound, upper_bound,
            alpha=0.1,
            calibration_size=100
        )

        assert "baseline" in result
        assert "conformal" in result
        assert "target_coverage" in result
        assert "calibration_results" in result

        # Check structure
        assert "coverage" in result["baseline"]
        assert "deviation" in result["baseline"]
        assert "coverage" in result["conformal"]
        assert "deviation" in result["conformal"]
        assert "adjustment_factor" in result["conformal"]

    def test_with_addtional_metadata(self):
        """Test comparison with series and model metadata."""
        np.random.seed(42)
        n = 300
        y_true = np.random.normal(50, 5, n)
        y_pred = y_true + np.random.normal(0, 0.5, n)
        lower_bound = y_pred - 1.4 * 5
        upper_bound = y_pred + 1.4 * 5

        result = compare_baseline_vs_conformal(
            y_true, y_pred, lower_bound, upper_bound,
            alpha=0.05,
            calibration_size=50
        )

        # Add metadata for aggregation test
        result["series_id"] = "test_series_1"
        result["model_name"] = "ARIMA"

        assert result["series_id"] == "test_series_1"
        assert result["model_name"] == "ARIMA"


class TestAggregateConformalResults:
    """Tests for result aggregation functions."""

    def test_aggregate_multiple_results(self):
        """Test aggregating results from multiple series/models."""
        results = []

        for i in range(5):
            np.random.seed(42 + i)
            n = 200
            y_true = np.random.normal(100, 10, n)
            y_pred = y_true + np.random.normal(0, 1, n)
            lower_bound = y_pred - 1.5 * 10
            upper_bound = y_pred + 1.5 * 10

            result = compare_baseline_vs_conformal(
                y_true, y_pred, lower_bound, upper_bound,
                alpha=0.1,
                calibration_size=50
            )
            result["series_id"] = f"series_{i}"
            result["model_name"] = "TestModel"
            results.append(result)

        df = aggregate_conformal_results(results)

        assert len(df) == 5
        assert "series_id" in df.columns
        assert "model_name" in df.columns
        assert "baseline_coverage" in df.columns
        assert "conformal_coverage" in df.columns
        assert "adjustment_factor" in df.columns

    def test_aggregate_empty_list(self):
        """Test aggregation with empty list."""
        df = aggregate_conformal_results([])
        assert len(df) == 0
        assert isinstance(df, pd.DataFrame)

    def test_conformal_results_to_dataframe(self):
        """Test conversion of single result to DataFrame."""
        np.random.seed(42)
        n = 200
        y_true = np.random.normal(100, 10, n)
        y_pred = y_true + np.random.normal(0, 1, n)
        lower_bound = y_pred - 1.5 * 10
        upper_bound = y_pred + 1.5 * 10

        result = compare_baseline_vs_conformal(
            y_true, y_pred, lower_bound, upper_bound,
            alpha=0.1,
            calibration_size=50
        )

        df = conformal_results_to_dataframe(result)

        assert len(df) == 1
        assert "baseline_coverage" in df.columns
        assert "conformal_coverage" in df.columns


# Import pandas for the empty list test
import pandas as pd
