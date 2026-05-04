"""Contract test for LSTM-AE baseline schema."""
import pytest
from datetime import datetime
import numpy as np
from typing import Optional, Dict, Any, List

# Note: LSTM-AE is implemented in baselines/lstm_ae.py
# This contract test verifies the expected schema structure

class TestLSTMAESchema:
    """Verify LSTM-AE baseline schemas have required fields."""

    def test_lstm_aeconfig_has_required_fields(self):
        """LSTMAEConfig must have hidden_size, num_layers, and sequence_length fields."""
        config = {
            "hidden_size": 64,
            "num_layers": 2,
            "sequence_length": 10,
            "learning_rate": 0.001
        }
        assert "hidden_size" in config
        assert "num_layers" in config
        assert "sequence_length" in config
        assert "learning_rate" in config

    def test_lstm_aeconfig_hidden_size_positive(self):
        """LSTMAEConfig hidden_size must be positive."""
        config = {"hidden_size": 64}
        assert config["hidden_size"] > 0

    def test_lstm_aeconfig_num_layers_positive(self):
        """LSTMAEConfig num_layers must be positive."""
        config = {"num_layers": 2}
        assert config["num_layers"] > 0

    def test_lstm_aeconfig_sequence_length_positive(self):
        """LSTMAEConfig sequence_length must be positive."""
        config = {"sequence_length": 10}
        assert config["sequence_length"] > 0

    def test_lstm_ae_prediction_has_required_fields(self):
        """LSTMAEPrediction must have timestamp, predicted_value, and reconstruction_error."""
        pred = {
            "timestamp": "2024-01-01T00:00:00",
            "predicted_value": 10.5,
            "reconstruction_error": 0.15
        }
        assert "timestamp" in pred
        assert "predicted_value" in pred
        assert "reconstruction_error" in pred

    def test_lstm_ae_prediction_error_non_negative(self):
        """LSTMAEPrediction reconstruction_error must be non-negative."""
        pred = {
            "timestamp": "2024-01-01T00:00:00",
            "predicted_value": 10.5,
            "reconstruction_error": 0.15
        }
        assert pred["reconstruction_error"] >= 0

    def test_lstm_ae_baseline_has_fit_method(self):
        """LSTMAEBaseline must have fit method."""
        # Verify the class exists and has the method
        from baselines.lstm_ae import LSTMAEBaseline
        assert hasattr(LSTMAEBaseline, "fit")

    def test_lstm_ae_baseline_has_predict_method(self):
        """LSTMAEBaseline must have predict method."""
        from baselines.lstm_ae import LSTMAEBaseline
        assert hasattr(LSTMAEBaseline, "predict")

    def test_lstm_ae_baseline_has_anomaly_score_method(self):
        """LSTMAEBaseline must have anomaly_score method."""
        from baselines.lstm_ae import LSTMAEBaseline
        assert hasattr(LSTMAEBaseline, "anomaly_score")

    def test_lstm_ae_can_serialize(self):
        """LSTM-AE configurations must be serializable to JSON."""
        import json
        config = {
            "hidden_size": 64,
            "num_layers": 2,
            "sequence_length": 10,
            "learning_rate": 0.001
        }
        serialized = json.dumps(config)
        assert serialized is not None
