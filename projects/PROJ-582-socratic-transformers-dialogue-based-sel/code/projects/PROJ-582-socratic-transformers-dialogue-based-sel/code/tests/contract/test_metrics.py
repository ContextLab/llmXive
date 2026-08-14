"""
Contract tests for the metrics utility.

These tests verify that the MetricCalculator and standalone functions
produce correct outputs for various input scenarios.
"""
import math
import pytest
from unittest.mock import MagicMock, patch
import torch

from src.utils.metrics import (
    MetricCalculator,
    compute_prediction_error_proxy,
    compute_calibration_error,
    compute_ngram_overlap,
)


@pytest.fixture
def mock_model_and_tokenizer():
    """Create mock model and tokenizer for testing."""
    model = MagicMock()
    tokenizer = MagicMock()
    return model, tokenizer


class TestPredictionErrorProxyOutput:
    """Tests for the compute_prediction_error_proxy function."""

    def test_identical_texts_zero_error(self):
        """Test that identical texts produce zero error."""
        text = "The answer is 42"
        error = compute_prediction_error_proxy(text, text)
        assert error == 0.0

    def test_completely_different_texts_high_error(self):
        """Test that completely different texts produce high error."""
        text1 = "The sky is blue"
        text2 = "The grass is green"
        error = compute_prediction_error_proxy(text1, text2)
        assert 0.5 <= error <= 1.0

    def test_empty_text_error(self):
        """Test that empty text produces maximum error."""
        error = compute_prediction_error_proxy("", "some text")
        assert error == 1.0

    def test_partial_match_lower_error(self):
        """Test that partial matches produce lower error."""
        text1 = "The answer is 42"
        text2 = "The answer is 43"
        error = compute_prediction_error_proxy(text1, text2)
        assert error < 1.0


class TestCalibrationErrorOutput:
    """Tests for the compute_calibration_error function."""

    def test_perfectly_calibrated_zero_error(self):
        """Test that perfectly calibrated predictions produce zero error."""
        predictions = [
            {"prediction": "yes", "confidence": 0.8, "is_correct": True},
            {"prediction": "no", "confidence": 0.2, "is_correct": False},
            {"prediction": "yes", "confidence": 0.9, "is_correct": True},
        ]
        error = compute_calibration_error(predictions)
        # With perfect calibration, error should be close to 0
        assert error < 0.1

    def test_miscalibrated_high_error(self):
        """Test that miscalibrated predictions produce higher error."""
        predictions = [
            {"prediction": "yes", "confidence": 0.9, "is_correct": False},
            {"prediction": "no", "confidence": 0.1, "is_correct": True},
        ]
        error = compute_calibration_error(predictions)
        assert error > 0.5

    def test_empty_predictions_zero_error(self):
        """Test that empty predictions list produces zero error."""
        error = compute_calibration_error([])
        assert error == 0.0


class TestNgramOverlapOutput:
    """Tests for the compute_ngram_overlap function."""

    def test_identical_texts_full_overlap(self):
        """Test that identical texts produce full overlap."""
        text = "the quick brown fox"
        overlap = compute_ngram_overlap(text, text)
        assert overlap == 1.0

    def test_completely_different_texts_zero_overlap(self):
        """Test that completely different texts produce zero overlap."""
        text1 = "the cat sat"
        text2 = "the dog ran"
        overlap = compute_ngram_overlap(text1, text2, n=2)
        # "the" is shared, so there might be some overlap
        # But bigrams should be different
        assert overlap < 0.5

    def test_no_overlap_different_words(self):
        """Test that texts with no common words produce zero overlap."""
        text1 = "apple banana cherry"
        text2 = "dog elephant frog"
        overlap = compute_ngram_overlap(text1, text2)
        assert overlap == 0.0

    def test_single_token_texts(self):
        """Test that single token texts produce zero overlap for n=2."""
        text1 = "cat"
        text2 = "dog"
        overlap = compute_ngram_overlap(text1, text2, n=2)
        assert overlap == 0.0


class TestMetricCalculatorOutput:
    """Tests for the MetricCalculator class methods."""

    def test_compute_accuracy_perfect(self):
        """Test perfect accuracy calculation."""
        calculator = MetricCalculator()
        predictions = [1, 2, 3, 4, 5]
        labels = [1, 2, 3, 4, 5]
        accuracy = calculator.compute_accuracy(predictions, labels)
        assert accuracy == 1.0

    def test_compute_accuracy_worst(self):
        """Test worst case accuracy calculation."""
        calculator = MetricCalculator()
        predictions = [1, 2, 3, 4, 5]
        labels = [2, 3, 4, 5, 6]
        accuracy = calculator.compute_accuracy(predictions, labels)
        assert accuracy == 0.0

    def test_compute_accuracy_partial(self):
        """Test partial accuracy calculation."""
        calculator = MetricCalculator()
        predictions = [1, 2, 3, 4, 5]
        labels = [1, 2, 0, 0, 5]
        accuracy = calculator.compute_accuracy(predictions, labels)
        assert accuracy == 0.6  # 3 out of 5 correct

    def test_compute_accuracy_with_ignore_index(self):
        """Test accuracy calculation with ignore_index."""
        calculator = MetricCalculator(ignore_index=-100)
        predictions = [1, 2, 3, 4, 5]
        labels = [1, 2, -100, 4, -100]
        accuracy = calculator.compute_accuracy(predictions, labels)
        # Only positions 0, 1, 3 are counted (3 total), all correct
        assert accuracy == 1.0

    def test_compute_accuracy_tensor_input(self):
        """Test accuracy calculation with tensor inputs."""
        calculator = MetricCalculator()
        predictions = torch.tensor([1, 2, 3, 4, 5])
        labels = torch.tensor([1, 2, 3, 4, 5])
        accuracy = calculator.compute_accuracy(predictions, labels)
        assert accuracy == 1.0

    def test_compute_ngram_overlap_method(self):
        """Test the n-gram overlap method."""
        calculator = MetricCalculator()
        text1 = "the quick brown fox"
        text2 = "the quick brown dog"
        overlap = calculator.compute_ngram_overlap(text1, text2, n=2)
        assert overlap > 0.0
        assert overlap < 1.0

    def test_compute_calibration_error_method(self):
        """Test the calibration error method."""
        calculator = MetricCalculator()
        predictions = [
            {"prediction": "yes", "confidence": 0.8, "is_correct": True},
            {"prediction": "no", "confidence": 0.2, "is_correct": False},
        ]
        error = calculator.compute_calibration_error(predictions)
        assert error >= 0.0
        assert error <= 1.0