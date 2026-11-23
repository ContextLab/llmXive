"""
Unit tests for gatekeeper/classifiers.py
"""
import pytest
from unittest.mock import patch, MagicMock
import torch

from gatekeeper.classifiers import (
    FrozenDistilBERTClassifier,
    ClassificationResult,
    run_inference,
    MODEL_ID,
    DEVICE,
)
from utils.profiling import reset_profiling


@pytest.fixture
def mock_tokenizer():
    mock = MagicMock()
    mock.return_value = {
        "input_ids": torch.tensor([[1, 2, 3]]),
        "attention_mask": torch.tensor([[1, 1, 1]]),
    }
    return mock


@pytest.fixture
def mock_model():
    mock = MagicMock()
    mock.logits = torch.tensor([[0.1, 0.9]])  # High confidence for class 1
    return mock


def test_classifier_initialization():
    """Test that classifier initializes with correct defaults."""
    clf = FrozenDistilBERTClassifier()
    assert clf.model_id == MODEL_ID
    assert clf.device.type == DEVICE
    assert not clf.is_loaded


@patch("gatekeeper.classifiers.DistilBertTokenizer.from_pretrained")
@patch("gatekeeper.classifiers.DistilBertForSequenceClassification.from_pretrained")
def test_load_model(mock_model_load, mock_tokenizer_load, mock_tokenizer, mock_model):
    """Test model loading logic."""
    mock_tokenizer_load.return_value = mock_tokenizer
    mock_model_load.return_value = mock_model

    clf = FrozenDistilBERTClassifier()
    clf.load()

    assert clf.is_loaded
    mock_model_load.assert_called_once()
    mock_tokenizer_load.assert_called_once()


@patch("gatekeeper.classifiers.DistilBertTokenizer.from_pretrained")
@patch("gatekeeper.classifiers.DistilBertForSequenceClassification.from_pretrained")
def test_run_inference_single(mock_model_load, mock_tokenizer_load, mock_tokenizer, mock_model):
    """Test inference on a single text."""
    mock_tokenizer_load.return_value = mock_tokenizer
    mock_model_load.return_value = mock_model

    clf = FrozenDistilBERTClassifier()
    clf.load()

    # Mock profiling functions to return 0 to avoid real tracing issues in test
    with patch("gatekeeper.classifiers.reset_profiling"), \
         patch("gatekeeper.classifiers.start_profiling"), \
         patch("gatekeeper.classifiers.stop_profiling"), \
         patch("gatekeeper.classifiers.get_peak_memory_mb", return_value=100.0):

        result = clf.classify("Test text")

    assert isinstance(result, ClassificationResult)
    assert result.label in ["allow", "deny"]
    assert isinstance(result.score, float)
    assert result.inference_time_ms >= 0.0
    assert result.peak_ram_mb >= 0.0


@patch("gatekeeper.classifiers.DistilBertTokenizer.from_pretrained")
@patch("gatekeeper.classifiers.DistilBertForSequenceClassification.from_pretrained")
def test_run_inference_batch(mock_model_load, mock_tokenizer_load, mock_tokenizer, mock_model):
    """Test inference on a batch of texts."""
    mock_tokenizer_load.return_value = mock_tokenizer
    mock_model_load.return_value = mock_model

    clf = FrozenDistilBERTClassifier()
    clf.load()

    texts = ["Text 1", "Text 2", "Text 3"]

    with patch("gatekeeper.classifiers.reset_profiling"), \
         patch("gatekeeper.classifiers.start_profiling"), \
         patch("gatekeeper.classifiers.stop_profiling"), \
         patch("gatekeeper.classifiers.get_peak_memory_mb", return_value=100.0):

        results = run_inference(clf, texts)

    assert len(results) == 3
    for res in results:
        assert "label" in res
        assert "score" in res
        assert "inference_time_ms" in res
        assert "peak_ram_mb" in res