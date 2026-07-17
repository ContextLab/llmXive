"""
Contract tests for metrics module output formats.
"""
import math
import pytest
from unittest.mock import MagicMock, patch
import torch

from src.utils.metrics import (
    compute_prediction_error_proxy,
    compute_calibration_error,
    compute_ngram_overlap,
    MetricCalculator
)


class TestPredictionErrorProxyOutput:
    """Test that prediction error proxy returns valid numeric output."""

    def test_returns_float(self, mock_model_and_tokenizer):
        """Test that the output is a float."""
        mock_model, mock_tokenizer = mock_model_and_tokenizer

        with patch.object(mock_tokenizer, '__call__', return_value={
            "input_ids": torch.tensor([[101, 2054, 2003, 102]]),
            "attention_mask": torch.tensor([[1, 1, 1, 1]])
        }):
            with patch.object(mock_tokenizer, 'encode', return_value=[101, 2054, 2003, 102]):
                result = compute_prediction_error_proxy(
                    mock_model, mock_tokenizer,
                    "What is 2+2?", "4"
                )
                assert isinstance(result, float)

    def test_returns_finite_value(self, mock_model_and_tokenizer):
        """Test that the output is a finite number."""
        mock_model, mock_tokenizer = mock_model_and_tokenizer

        with patch.object(mock_tokenizer, '__call__', return_value={
            "input_ids": torch.tensor([[101, 2054, 2003, 102]]),
            "attention_mask": torch.tensor([[1, 1, 1, 1]])
        }):
            with patch.object(mock_tokenizer, 'encode', return_value=[101, 2054, 2003, 102]):
                result = compute_prediction_error_proxy(
                    mock_model, mock_tokenizer,
                    "What is 2+2?", "4"
                )
                assert math.isfinite(result)


class TestCalibrationErrorOutput:
    """Test that calibration error returns valid numeric output."""

    def test_returns_float(self):
        """Test that the output is a float."""
        result = compute_calibration_error([0.5, 0.6], [True, False])
        assert isinstance(result, float)

    def test_returns_non_negative(self):
        """Test that the output is non-negative."""
        result = compute_calibration_error([0.5, 0.6], [True, False])
        assert result >= 0.0

    def test_returns_le_one(self):
        """Test that the output is <= 1.0."""
        result = compute_calibration_error([0.5, 0.6], [True, False])
        assert result <= 1.0


class TestNgramOverlapOutput:
    """Test that n-gram overlap returns valid numeric output."""

    def test_returns_float(self):
        """Test that the output is a float."""
        result = compute_ngram_overlap("hello world", "hello world", n=2)
        assert isinstance(result, float)

    def test_returns_between_zero_and_one(self):
        """Test that the output is between 0 and 1."""
        result = compute_ngram_overlap("hello world", "hello world", n=2)
        assert 0.0 <= result <= 1.0


class TestMetricCalculatorOutput:
    """Test MetricCalculator method outputs."""

    def test_compute_error_proxy_returns_float(self, mock_model_and_tokenizer):
        """Test that compute_error_proxy returns a float."""
        mock_model, mock_tokenizer = mock_model_and_tokenizer
        calculator = MetricCalculator()
        calculator.set_model(mock_model, mock_tokenizer)

        with patch.object(mock_tokenizer, '__call__', return_value={
            "input_ids": torch.tensor([[101, 2054, 2003, 102]]),
            "attention_mask": torch.tensor([[1, 1, 1, 1]])
        }):
            with patch.object(mock_tokenizer, 'encode', return_value=[101, 2054, 2003, 102]):
                result = calculator.compute_error_proxy("hello", "world")
                assert isinstance(result, float)

    def test_compute_calibration_returns_float(self):
        """Test that compute_calibration returns a float."""
        calculator = MetricCalculator()
        result = calculator.compute_calibration([0.5, 0.6], [True, False])
        assert isinstance(result, float)

    def test_compute_overlap_returns_float(self):
        """Test that compute_overlap returns a float."""
        calculator = MetricCalculator()
        result = calculator.compute_overlap("hello world", "hello world", n=2)
        assert isinstance(result, float)


@pytest.fixture
def mock_model_and_tokenizer():
    """Create mock model and tokenizer for testing."""
    mock_model = MagicMock()
    mock_tokenizer = MagicMock()

    mock_tokenizer.return_value = {
        "input_ids": torch.tensor([[101, 2054, 2003, 102]]),
        "attention_mask": torch.tensor([[1, 1, 1, 1]])
    }
    mock_tokenizer.encode.return_value = [101, 2054, 2003, 102]

    mock_model.return_value = MagicMock(
        logits=torch.randn(1, 4, 1000),
        loss=torch.tensor(0.5)
    )

    return mock_model, mock_tokenizer
