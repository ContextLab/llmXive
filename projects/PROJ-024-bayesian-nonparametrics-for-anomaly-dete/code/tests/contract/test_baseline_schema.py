"""Contract test for baseline configurations and predictions schemas."""
import pytest
from datetime import datetime
import numpy as np
from typing import Optional, Dict, Any, List

# Import from the correct paths per API surface
from baselines.arima import ARIMAConfig, ARIMAPrediction, ARIMABaseline
from baselines.moving_average import MovingAverageConfig, MovingAveragePrediction, MovingAverageBaseline

class TestARIMASchema:
    """Verify ARIMA baseline schemas have required fields."""

    def test_arimaconfig_has_required_fields(self):
        """ARIMAConfig must have order and seasonal_order fields."""
        config = ARIMAConfig(order=(1, 1, 1), seasonal_order=(1, 1, 1, 12))
        assert hasattr(config, "order")
        assert hasattr(config, "seasonal_order")

    def test_arimaprediction_has_required_fields(self):
        """ARIMAPrediction must have timestamp, predicted_value, and confidence_interval."""
        pred = ARIMAPrediction(
            timestamp=datetime(2024, 1, 1),
            predicted_value=10.5,
            confidence_interval=(8.0, 13.0)
        )
        assert hasattr(pred, "timestamp")
        assert hasattr(pred, "predicted_value")
        assert hasattr(pred, "confidence_interval")

    def test_arimaprediction_confidence_is_tuple(self):
        """ARIMAPrediction confidence_interval must be a tuple."""
        pred = ARIMAPrediction(
            timestamp=datetime(2024, 1, 1),
            predicted_value=10.5,
            confidence_interval=(8.0, 13.0)
        )
        assert isinstance(pred.confidence_interval, tuple)
        assert len(pred.confidence_interval) == 2

    def test_arimabaseline_has_fit_method(self):
        """ARIMABaseline must have fit method."""
        assert hasattr(ARIMABaseline, "fit")

    def test_arimabaseline_has_predict_method(self):
        """ARIMABaseline must have predict method."""
        assert hasattr(ARIMABaseline, "predict")

    def test_arimabaseline_has_anomaly_score_method(self):
        """ARIMABaseline must have anomaly_score method."""
        assert hasattr(ARIMABaseline, "anomaly_score")

class TestMovingAverageSchema:
    """Verify Moving Average baseline schemas have required fields."""

    def test_maconfig_has_required_fields(self):
        """MovingAverageConfig must have window_size field."""
        config = MovingAverageConfig(window_size=10)
        assert hasattr(config, "window_size")

    def test_maprediction_has_required_fields(self):
        """MovingAveragePrediction must have timestamp, predicted_value, and actual_value."""
        pred = MovingAveragePrediction(
            timestamp=datetime(2024, 1, 1),
            predicted_value=10.5,
            actual_value=11.0
        )
        assert hasattr(pred, "timestamp")
        assert hasattr(pred, "predicted_value")
        assert hasattr(pred, "actual_value")

    def test_mabaseline_has_fit_method(self):
        """MovingAverageBaseline must have fit method."""
        assert hasattr(MovingAverageBaseline, "fit")

    def test_mabaseline_has_predict_method(self):
        """MovingAverageBaseline must have predict method."""
        assert hasattr(MovingAverageBaseline, "predict")

    def test_mabaseline_has_anomaly_score_method(self):
        """MovingAverageBaseline must have anomaly_score method."""
        assert hasattr(MovingAverageBaseline, "anomaly_score")

    def test_maconfig_window_size_positive(self):
        """MovingAverageConfig window_size must be positive."""
        config = MovingAverageConfig(window_size=10)
        assert config.window_size > 0
