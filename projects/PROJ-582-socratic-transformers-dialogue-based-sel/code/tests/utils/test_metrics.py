"""
Tests for the prediction error proxy calculator and related metrics.
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
    MetricCalculator,
)


@pytest.fixture
def mock_model_and_tokenizer():
    """Create mock model and tokenizer for testing."""
    model = MagicMock(spec=PreTrainedModel)
    tokenizer = MagicMock(spec=PreTrainedTokenizer)

    # Mock tokenizer behavior
    def mock_encode(text, return_tensors="pt", truncation=False, add_special_tokens=False):
        # Simple mock: split by spaces and convert to IDs
        tokens = text.split()
        ids = [hash(t) % 1000 for t in tokens]  # Deterministic mock IDs
        return {"input_ids": torch.tensor([ids]), "attention_mask": torch.ones((1, len(ids)))}

    tokenizer.side_effect = mock_encode
    tokenizer.return_value = mock_encode("", return_tensors="pt")

    # Mock model outputs
    logits = torch.randn(1, 10, 1000)  # (batch, seq_len, vocab_size)
    outputs = MagicMock()
    outputs.logits = logits
    model.return_value = outputs

    return model, tokenizer


def test_compute_prediction_error_proxy_basic(mock_model_and_tokenizer):
    """Test basic computation of prediction error proxy."""
    model, tokenizer = mock_model_and_tokenizer
    prompt = "What is 2+2?"
    response = "4"

    error = compute_prediction_error_proxy(model, tokenizer, prompt, response)

    assert isinstance(error, float)
    assert error >= 0  # Negative log-likelihood should be non-negative


def test_compute_prediction_error_proxy_empty_response(mock_model_and_tokenizer):
    """Test that empty response returns infinity."""
    model, tokenizer = mock_model_and_tokenizer
    prompt = "Hello"
    response = ""

    error = compute_prediction_error_proxy(model, tokenizer, prompt, response)

    assert math.isinf(error)


def test_compute_calibration_error_perfect_calibration():
    """Test calibration error with perfectly calibrated predictions."""
    # All predictions with 0.8 confidence are correct 80% of the time
    probs = [0.8, 0.8, 0.8, 0.8, 0.2, 0.2, 0.2, 0.2]
    correct = [True, True, True, False, False, False, False, False]

    ece = compute_calibration_error(probs, correct, bins=2)

    # Should be close to 0 (perfect calibration)
    assert ece < 0.1


def test_compute_calibration_error_miscalibrated():
    """Test calibration error with poorly calibrated predictions."""
    # High confidence predictions that are mostly wrong
    probs = [0.9, 0.9, 0.9, 0.9, 0.9]
    correct = [False, False, False, False, False]

    ece = compute_calibration_error(probs, correct, bins=2)

    # Should be high (poor calibration)
    assert ece > 0.5


def test_compute_ngram_overlap_identical_texts():
    """Test n-gram overlap with identical texts."""
    text = "the quick brown fox"
    overlap = compute_ngram_overlap(text, text, n=2)

    assert overlap == 1.0


def test_compute_ngram_overlap_no_overlap():
    """Test n-gram overlap with completely different texts."""
    text1 = "the quick brown fox"
    text2 = "a slow red dog"
    overlap = compute_ngram_overlap(text1, text2, n=2)

    # Should be 0 or very low
    assert overlap == 0.0


def test_metric_calculator_init():
    """Test MetricCalculator initialization."""
    model = MagicMock(spec=PreTrainedModel)
    tokenizer = MagicMock(spec=PreTrainedTokenizer)

    calculator = MetricCalculator(model, tokenizer)

    assert calculator.model == model
    assert calculator.tokenizer == tokenizer


def test_metric_calculator_compute_error_proxy(mock_model_and_tokenizer):
    """Test MetricCalculator's error proxy method."""
    model, tokenizer = mock_model_and_tokenizer
    calculator = MetricCalculator(model, tokenizer)

    prompt = "Test prompt"
    response = "Test response"

    error = calculator.compute_error_proxy(prompt, response)

    assert isinstance(error, float)
    assert error >= 0
