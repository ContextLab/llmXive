"""
Unit tests for baseline scoring logic.

Tests that ARIMA and Moving Average baselines produce scores
on test data within expected ranges (US2 acceptance criteria).
"""
import pytest
import numpy as np
from pathlib import Path
import sys

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from src.baselines.arima import ARIMAConfig, ARIMABaseline, create_baseline
from src.baselines.moving_average import (
    MovingAverageConfig,
    MovingAverageBaseline,
    create_baseline as create_ma_baseline,
)


class TestARIMAScoring:
    """Unit tests for ARIMA baseline scoring logic."""

    def test_arima_baseline_creation(self):
        """Verify ARIMA baseline can be instantiated with valid config."""
        config = ARIMAConfig(
            order=(1, 1, 1),
            seasonal_order=(0, 0, 0, 0),
            trend="c",
            start_params=None,
            enforce_stationarity=True,
            enforce_invertibility=True,
            maxiter=100,
            disp=False,
        )
        baseline = create_baseline(config)

        assert baseline is not None
        assert baseline.config.order == (1, 1, 1)

    def test_arima_score_range_on_synthetic_data(self):
        """Verify ARIMA scores are within expected numerical range."""
        # Generate synthetic time series data
        np.random.seed(42)
        n_points = 100
        # Normal signal with small noise
        base_signal = np.sin(np.linspace(0, 4 * np.pi, n_points))
        noise = np.random.normal(0, 0.1, n_points)
        time_series = base_signal + noise

        config = ARIMAConfig(
            order=(1, 1, 1),
            seasonal_order=(0, 0, 0, 0),
            trend="c",
            maxiter=50,
            disp=False,
        )
        baseline = create_baseline(config)

        # Train on first 80% of data
        train_size = int(n_points * 0.8)
        baseline.fit(time_series[:train_size])

        # Score on remaining data
        scores = baseline.score(time_series[train_size:])

        # Scores should be numpy array
        assert isinstance(scores, np.ndarray)
        assert len(scores) == n_points - train_size

        # Scores should be finite (no NaN or Inf)
        assert np.all(np.isfinite(scores))

        # Scores should be in reasonable range for anomaly scores
        # (typically positive, not extremely large)
        assert np.all(scores >= 0)
        assert np.all(scores < 1000)  # Sanity check for extreme values

    def test_arima_anomaly_detection_capability(self):
        """Verify ARIMA can detect injected anomalies."""
        np.random.seed(123)
        n_points = 50

        # Normal signal
        base_signal = np.sin(np.linspace(0, 2 * np.pi, n_points))
        normal_data = base_signal + np.random.normal(0, 0.05, n_points)

        # Inject anomaly at index 30
        anomaly_data = normal_data.copy()
        anomaly_data[30] = anomaly_data[30] + 3.0  # Large spike

        config = ARIMAConfig(
            order=(1, 1, 1),
            maxiter=50,
            disp=False,
        )
        baseline = create_baseline(config)

        # Train on data before anomaly
        baseline.fit(anomaly_data[:25])

        # Score on data including anomaly
        scores = baseline.score(anomaly_data[25:])

        # Anomaly at index 30 (relative index 5 in scores)
        # Should have higher score than surrounding points
        anomaly_idx = 5
        surrounding_scores = np.concatenate([
            scores[max(0, anomaly_idx - 2):anomaly_idx],
            scores[anomaly_idx + 1:min(len(scores), anomaly_idx + 3)]
        ])

        # Anomaly score should be higher than median of surrounding
        assert scores[anomaly_idx] > np.median(surrounding_scores)


class TestMovingAverageScoring:
    """Unit tests for Moving Average baseline scoring logic."""

    def test_moving_average_baseline_creation(self):
        """Verify Moving Average baseline can be instantiated with valid config."""
        config = MovingAverageConfig(
            window_size=10,
            threshold_multiplier=2.0,
            min_data_points=5,
        )
        baseline = create_ma_baseline(config)

        assert baseline is not None
        assert baseline.config.window_size == 10

    def test_ma_score_range_on_synthetic_data(self):
        """Verify Moving Average scores are within expected numerical range."""
        np.random.seed(42)
        n_points = 100

        # Generate synthetic time series
        base_signal = np.sin(np.linspace(0, 4 * np.pi, n_points))
        noise = np.random.normal(0, 0.1, n_points)
        time_series = base_signal + noise

        config = MovingAverageConfig(
            window_size=10,
            threshold_multiplier=2.0,
        )
        baseline = create_ma_baseline(config)

        # Fit and score
        baseline.fit(time_series)
        scores = baseline.score(time_series)

        # Scores should be numpy array
        assert isinstance(scores, np.ndarray)
        assert len(scores) == n_points

        # Scores should be finite
        assert np.all(np.isfinite(scores))

        # Scores should be non-negative (typical for anomaly scores)
        assert np.all(scores >= 0)

    def test_ma_anomaly_detection_capability(self):
        """Verify Moving Average can detect injected anomalies."""
        np.random.seed(123)
        n_points = 50

        # Normal signal
        base_signal = np.sin(np.linspace(0, 2 * np.pi, n_points))
        normal_data = base_signal + np.random.normal(0, 0.05, n_points)

        # Inject anomaly at index 30
        anomaly_data = normal_data.copy()
        anomaly_data[30] = anomaly_data[30] + 3.0  # Large spike

        config = MovingAverageConfig(
            window_size=5,
            threshold_multiplier=2.0,
        )
        baseline = create_ma_baseline(config)

        baseline.fit(anomaly_data)
        scores = baseline.score(anomaly_data)

        # Anomaly at index 30 should have higher score
        anomaly_score = scores[30]
        surrounding_scores = np.concatenate([
            scores[max(0, 25):30],
            scores[31:min(len(scores), 35)]
        ])

        # Anomaly score should be higher than most surrounding points
        assert anomaly_score > np.percentile(surrounding_scores, 75)

    def test_ma_with_constant_signal(self):
        """Verify Moving Average handles constant signal without errors."""
        np.random.seed(42)
        constant_data = np.ones(50) * 5.0

        config = MovingAverageConfig(
            window_size=5,
            threshold_multiplier=2.0,
        )
        baseline = create_ma_baseline(config)

        baseline.fit(constant_data)
        scores = baseline.score(constant_data)

        # Should not raise errors
        assert isinstance(scores, np.ndarray)
        assert len(scores) == 50
        # All scores should be zero or very small for constant data
        assert np.all(scores < 0.001)


class TestBaselineScoringIntegration:
    """Integration tests comparing baseline scoring behaviors."""

    def test_both_baselines_produce_scores(self):
        """Verify both baselines produce scores on same data."""
        np.random.seed(42)
        n_points = 50
        time_series = np.sin(np.linspace(0, 2 * np.pi, n_points)) + np.random.normal(0, 0.1, n_points)

        # ARIMA
        arima_config = ARIMAConfig(order=(1, 1, 1), maxiter=50, disp=False)
        arima_baseline = create_baseline(arima_config)
        arima_baseline.fit(time_series[:40])
        arima_scores = arima_baseline.score(time_series[40:])

        # Moving Average
        ma_config = MovingAverageConfig(window_size=5, threshold_multiplier=2.0)
        ma_baseline = create_ma_baseline(ma_config)
        ma_baseline.fit(time_series)
        ma_scores = ma_baseline.score(time_series)

        # Both should produce valid score arrays
        assert isinstance(arima_scores, np.ndarray)
        assert isinstance(ma_scores, np.ndarray)
        assert np.all(np.isfinite(arima_scores))
        assert np.all(np.isfinite(ma_scores))

    def test_baseline_scores_correlate_with_anomalies(self):
        """Verify baseline scores increase at anomaly locations."""
        np.random.seed(42)
        n_points = 50

        # Normal signal
        normal_data = np.sin(np.linspace(0, 2 * np.pi, n_points)) + np.random.normal(0, 0.05, n_points)

        # Create data with anomaly at index 25
        anomaly_data = normal_data.copy()
        anomaly_data[25] += 3.0

        # ARIMA
        arima_config = ARIMAConfig(order=(1, 1, 1), maxiter=50, disp=False)
        arima_baseline = create_baseline(arima_config)
        arima_baseline.fit(anomaly_data[:20])
        arima_scores = arima_baseline.score(anomaly_data[20:])

        # Moving Average
        ma_config = MovingAverageConfig(window_size=5, threshold_multiplier=2.0)
        ma_baseline = create_ma_baseline(ma_config)
        ma_baseline.fit(anomaly_data)
        ma_scores = ma_baseline.score(anomaly_data)

        # Both baselines should detect the anomaly
        arima_anomaly_idx = 5  # 25 - 20
        ma_anomaly_idx = 25

        # Anomaly scores should be in top 20% of all scores
        arima_threshold = np.percentile(arima_scores, 80)
        ma_threshold = np.percentile(ma_scores, 80)

        assert arima_scores[arima_anomaly_idx] >= arima_threshold
        assert ma_scores[ma_anomaly_idx] >= ma_threshold