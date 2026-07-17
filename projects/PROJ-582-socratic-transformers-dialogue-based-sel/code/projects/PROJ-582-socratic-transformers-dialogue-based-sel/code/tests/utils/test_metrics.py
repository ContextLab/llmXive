"""
Tests for the metrics module.
"""
import math
import pytest
import torch
from unittest.mock import MagicMock, patch
from transformers import PreTrainedModel, PreTrainedTokenizer

from src.utils.metrics import (
    compute_prediction_error_proxy,
    compute_calibration_error,
    compute_ngram_overlap,
    MetricCalculator
)


@pytest.fixture
def mock_model_and_tokenizer():
    """Create mock model and tokenizer for testing."""
    mock_model = MagicMock(spec=PreTrainedModel)
    mock_tokenizer = MagicMock(spec=PreTrainedTokenizer)

    # Mock tokenizer behavior
    mock_tokenizer.return_value = {
        "input_ids": torch.tensor([[101, 2054, 2003, 102]]),  # [CLS] hello world [SEP]
        "attention_mask": torch.tensor([[1, 1, 1, 1]])
    }
    mock_tokenizer.encode.return_value = [101, 2054, 2003, 102]
    mock_tokenizer.convert_ids_to_tokens.return_value = ["[CLS]", "hello", "world", "[SEP]"]

    # Mock model behavior
    mock_logits = torch.randn(1, 4, 1000)  # batch=1, seq_len=4, vocab=1000
    mock_model.return_value = MagicMock(
        logits=mock_logits,
        loss=torch.tensor(0.5)
    )

    return mock_model, mock_tokenizer


def test_compute_prediction_error_proxy_basic(mock_model_and_tokenizer):
    """Test basic prediction error proxy computation."""
    mock_model, mock_tokenizer = mock_model_and_tokenizer

    # Patch the tokenizer to return consistent results
    with patch.object(mock_tokenizer, '__call__', return_value={
        "input_ids": torch.tensor([[101, 2054, 2003, 102]]),
        "attention_mask": torch.tensor([[1, 1, 1, 1]])
    }):
        with patch.object(mock_tokenizer, 'encode', return_value=[101, 2054, 2003, 102]):
            result = compute_prediction_error_proxy(
                mock_model, mock_tokenizer,
                "hello", "world"
            )

            # Result should be a finite float
            assert isinstance(result, float)
            assert math.isfinite(result)


def test_compute_prediction_error_proxy_empty_response(mock_model_and_tokenizer):
    """Test that empty answer raises ValueError."""
    mock_model, mock_tokenizer = mock_model_and_tokenizer

    with patch.object(mock_tokenizer, '__call__', return_value={
        "input_ids": torch.tensor([[101, 102]]),  # Only [CLS] [SEP]
        "attention_mask": torch.tensor([[1, 1]])
    }):
        with patch.object(mock_tokenizer, 'encode', return_value=[101, 102]):
            with pytest.raises(ValueError, match="Answer tokenized to empty"):
                compute_prediction_error_proxy(
                    mock_model, mock_tokenizer,
                    "hello", ""
                )


def test_compute_calibration_error_perfect_calibration():
    """Test calibration error with perfect calibration."""
    # All predictions match outcomes
    predicted_probs = [0.9, 0.8, 0.7, 0.6]
    actual_outcomes = [True, True, True, True]

    error = compute_calibration_error(predicted_probs, actual_outcomes)
    # Should be close to 0 (perfect calibration)
    assert error < 0.1


def test_compute_calibration_error_miscalibrated():
    """Test calibration error with miscalibrated predictions."""
    # High confidence but wrong outcomes
    predicted_probs = [0.9, 0.9, 0.9, 0.9]
    actual_outcomes = [False, False, False, False]

    error = compute_calibration_error(predicted_probs, actual_outcomes)
    # Should be high (close to 0.9)
    assert error > 0.5


def test_compute_ngram_overlap_identical_texts():
    """Test n-gram overlap with identical texts."""
    text = "the quick brown fox"
    overlap = compute_ngram_overlap(text, text, n=3)
    assert overlap == 1.0


def test_compute_ngram_overlap_no_overlap():
    """Test n-gram overlap with completely different texts."""
    text1 = "the quick brown fox"
    text2 = "lazy dog sleeps"
    overlap = compute_ngram_overlap(text1, text2, n=3)
    assert overlap == 0.0


def test_metric_calculator_init():
    """Test MetricCalculator initialization."""
    calculator = MetricCalculator()
    assert calculator.model is None
    assert calculator.tokenizer is None


def test_metric_calculator_compute_error_proxy(mock_model_and_tokenizer):
    """Test MetricCalculator.compute_error_proxy."""
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
            assert math.isfinite(result)
