"""
Contract tests for the metrics utility module.
"""

import math
import pytest
from unittest.mock import MagicMock, patch

import torch

from src.utils.metrics import (
    MetricCalculator,
    compute_prediction_error_proxy,
    compute_calibration_error,
    compute_ngram_overlap
)


@pytest.fixture
def mock_model_and_tokenizer():
    """Create mock model and tokenizer for testing."""
    mock_model = MagicMock()
    mock_model.device = torch.device('cpu')
    mock_tokenizer = MagicMock()
    return mock_model, mock_tokenizer


class TestPredictionErrorProxyOutput:
    """Tests for compute_prediction_error_proxy function."""

    def test_returns_tuple_of_three(self):
        """Function should return a tuple of 3 floats."""
        predictions = [1.0, 2.0, 3.0]
        targets = [1.0, 2.0, 3.0]
        result = compute_prediction_error_proxy(predictions, targets)

        assert isinstance(result, tuple)
        assert len(result) == 3

    def test_perfect_prediction_zero_error(self):
        """Perfect predictions should yield zero error."""
        predictions = [1.0, 2.0, 3.0]
        targets = [1.0, 2.0, 3.0]
        mae, mse, rmse = compute_prediction_error_proxy(predictions, targets)

        assert mae == 0.0
        assert mse == 0.0
        assert rmse == 0.0

    def test_constant_error(self):
        """Constant error should produce consistent metrics."""
        predictions = [2.0, 3.0, 4.0]
        targets = [1.0, 2.0, 3.0]
        mae, mse, rmse = compute_prediction_error_proxy(predictions, targets)

        assert mae == 1.0
        assert mse == 1.0
        assert rmse == 1.0


class TestCalibrationErrorOutput:
    """Tests for compute_calibration_error function."""

    def test_perfect_calibration_zero_ece(self):
        """Perfectly calibrated predictions should have zero ECE."""
        predicted_probs = [0.9, 0.8, 0.1, 0.2]
        correct_flags = [True, True, False, False]
        ece = compute_calibration_error(predicted_probs, correct_flags)

        assert ece == 0.0

    def test_perfectly_uncalibrated(self):
        """Perfectly mis-calibrated predictions should have high ECE."""
        predicted_probs = [0.9, 0.9, 0.1, 0.1]
        correct_flags = [False, False, True, True]
        ece = compute_calibration_error(predicted_probs, correct_flags)

        # All predictions are wrong with high confidence
        assert ece > 0.8

    def test_empty_input(self):
        """Empty input should return zero error."""
        ece = compute_calibration_error([], [])
        assert ece == 0.0


class TestNgramOverlapOutput:
    """Tests for compute_ngram_overlap function."""

    def test_identical_texts(self):
        """Identical texts should have overlap of 1.0."""
        text = "the quick brown fox"
        overlap = compute_ngram_overlap(text, text)
        assert overlap == 1.0

    def test_no_overlap(self):
        """Completely different texts should have overlap of 0.0."""
        text1 = "the quick brown fox"
        text2 = "a completely different sentence"
        overlap = compute_ngram_overlap(text1, text2, n=2)
        assert overlap == 0.0

    def test_partial_overlap(self):
        """Partially overlapping texts should have intermediate overlap."""
        text1 = "the quick brown fox"
        text2 = "the quick red fox"
        overlap = compute_ngram_overlap(text1, text2, n=2)
        assert 0.0 < overlap < 1.0

    def test_empty_texts(self):
        """Empty texts should return 1.0 (both empty)."""
        overlap = compute_ngram_overlap("", "")
        assert overlap == 1.0


class TestMetricCalculatorOutput:
    """Tests for MetricCalculator class."""

    def test_accuracy_perfect(self, mock_model_and_tokenizer):
        """Perfect predictions should yield accuracy of 1.0."""
        model, tokenizer = mock_model_and_tokenizer
        calculator = MetricCalculator(model, tokenizer)

        predictions = [1, 2, 3, 4, 5]
        labels = [1, 2, 3, 4, 5]
        accuracy = calculator.compute_accuracy(predictions, labels)

        assert accuracy == 1.0

    def test_accuracy_zero(self, mock_model_and_tokenizer):
        """Completely wrong predictions should yield accuracy of 0.0."""
        model, tokenizer = mock_model_and_tokenizer
        calculator = MetricCalculator(model, tokenizer)

        predictions = [1, 2, 3, 4, 5]
        labels = [6, 7, 8, 9, 10]
        accuracy = calculator.compute_accuracy(predictions, labels)

        assert accuracy == 0.0

    def test_accuracy_with_ignore_index(self, mock_model_and_tokenizer):
        """Ignore index should be excluded from accuracy calculation."""
        model, tokenizer = mock_model_and_tokenizer
        calculator = MetricCalculator(model, tokenizer)

        predictions = [1, 2, -100, 4, 5]
        labels = [1, 2, -100, 4, 10]  # Last one wrong
        accuracy = calculator.compute_accuracy(predictions, labels, ignore_index=-100)

        # Should only consider 4 positions: 3 correct, 1 wrong
        assert accuracy == 0.75

    def test_mismatched_lengths_raises(self, mock_model_and_tokenizer):
        """Mismatched lengths should raise ValueError."""
        model, tokenizer = mock_model_and_tokenizer
        calculator = MetricCalculator(model, tokenizer)

        predictions = [1, 2, 3]
        labels = [1, 2]

        with pytest.raises(ValueError):
            calculator.compute_accuracy(predictions, labels)

    def test_perplexity_positive(self, mock_model_and_tokenizer):
        """Perplexity should always be positive."""
        model, tokenizer = mock_model_and_tokenizer
        calculator = MetricCalculator(model, tokenizer)

        # Mock the model's forward pass to return a fixed loss
        mock_output = MagicMock()
        mock_output.loss = torch.tensor(0.5)
        model.return_value = mock_output

        input_ids = torch.tensor([[1, 2, 3]])
        labels = torch.tensor([[1, 2, 3]])

        perplexity = calculator.compute_perplexity(input_ids, labels)

        assert perplexity > 1.0

    def test_perplexity_matches_exp_loss(self, mock_model_and_tokenizer):
        """Perplexity should equal exp(loss)."""
        model, tokenizer = mock_model_and_tokenizer
        calculator = MetricCalculator(model, tokenizer)

        mock_output = MagicMock()
        mock_output.loss = torch.tensor(1.0)
        model.return_value = mock_output

        input_ids = torch.tensor([[1, 2, 3]])
        labels = torch.tensor([[1, 2, 3]])

        perplexity = calculator.compute_perplexity(input_ids, labels)

        assert math.isclose(perplexity, math.exp(1.0), rel_tol=1e-5)