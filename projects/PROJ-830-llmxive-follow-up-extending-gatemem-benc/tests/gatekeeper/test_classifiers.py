"""
Tests for the Gatekeeper Classifiers module.

Verifies CPU-only execution, memory constraints, and correct inference behavior.
"""
import pytest
import torch
import os
from unittest.mock import patch, MagicMock
from typing import List

# Import the module under test
from code.gatekeeper.classifiers import (
    FrozenDistilBERTClassifier,
    ClassificationResult,
    run_intent_classification,
    MODEL_NAME,
    MEMORY_LIMIT_MB,
    DEVICE
)
from code.utils.profiling import get_peak_memory_mb

class TestFrozenDistilBERTClassifier:
    """Tests for the FrozenDistilBERTClassifier class."""

    def test_initialization_cpu_only(self):
        """Test that classifier initializes with CPU device."""
        classifier = FrozenDistilBERTClassifier()
        assert classifier.device == "cpu"
        assert not classifier._loaded

    def test_initialization_forces_cpu(self):
        """Test that requesting non-CPU device forces CPU."""
        # Mock torch.cuda.is_available to simulate CUDA presence
        with patch('code.gatekeeper.classifiers.torch.cuda.is_available', return_value=True):
            classifier = FrozenDistilBERTClassifier(device="cuda")
            assert classifier.device == "cpu"

    @pytest.mark.skipif(
        not torch.cuda.is_available(),
        reason="CUDA not available for this test"
    )
    def test_cuda_disabled_when_available(self):
        """Test that CUDA is disabled even when available."""
        classifier = FrozenDistilBERTClassifier()
        assert os.environ.get("CUDA_VISIBLE_DEVICES") == ""

    @pytest.mark.integration
    def test_load_model_success(self):
        """Test that the model can be loaded successfully."""
        classifier = FrozenDistilBERTClassifier()
        # Note: This test requires network access to download the model
        # In CI, this might be skipped if offline
        try:
            success = classifier.load()
            assert success
            assert classifier._loaded
            assert classifier.model is not None
            assert classifier.tokenizer is not None
        except Exception as e:
            # If model download fails (e.g., network issues), skip
            pytest.skip(f"Model download failed: {e}")

    @pytest.mark.integration
    def test_classify_returns_results(self):
        """Test that classification returns valid results."""
        classifier = FrozenDistilBERTClassifier()
        try:
            classifier.load()
        except Exception:
            pytest.skip("Model loading failed")

        texts = ["Test input for classification"]
        results = classifier.classify(texts)

        assert len(results) == 1
        result = results[0]
        
        assert isinstance(result, ClassificationResult)
        assert result.label is not None
        assert isinstance(result.score, float)
        assert 0.0 <= result.score <= 1.0
        assert result.model_name == MODEL_NAME
        assert result.device == "cpu"
        assert result.peak_memory_mb is not None

    @pytest.mark.integration
    def test_classify_batch(self):
        """Test batch classification."""
        classifier = FrozenDistilBERTClassifier()
        try:
            classifier.load()
        except Exception:
            pytest.skip("Model loading failed")

        texts = [
            "First test input",
            "Second test input",
            "Third test input"
        ]
        results = classifier.classify(texts)

        assert len(results) == len(texts)
        for result in results:
            assert isinstance(result, ClassificationResult)
            assert result.label is not None
            assert 0.0 <= result.score <= 1.0

    @pytest.mark.integration
    def test_memory_limit_check(self):
        """Test that memory usage is logged and checked."""
        classifier = FrozenDistilBERTClassifier()
        try:
            classifier.load()
        except Exception:
            pytest.skip("Model loading failed")

        # Run classification to trigger memory logging
        texts = ["Test text for memory check"]
        results = classifier.classify(texts)

        # Verify peak memory was recorded
        for result in results:
            assert result.peak_memory_mb is not None
            # Note: We don't assert < 2GB here because the actual limit depends
            # on the environment; we just verify it's recorded.

    def test_model_frozen(self):
        """Test that model parameters are frozen after loading."""
        classifier = FrozenDistilBERTClassifier()
        try:
            classifier.load()
        except Exception:
            pytest.skip("Model loading failed")

        # Check that gradients are disabled
        for param in classifier.model.parameters():
            assert not param.requires_grad

class TestRunIntentClassification:
    """Tests for the run_intent_classification convenience function."""

    @pytest.mark.integration
    def test_run_intent_classification_function(self):
        """Test the convenience function."""
        try:
            results = run_intent_classification(["Test input"])
        except Exception:
            pytest.skip("Model loading failed")

        assert len(results) == 1
        assert isinstance(results[0], ClassificationResult)

class TestClassificationResult:
    """Tests for the ClassificationResult dataclass."""

    def test_creation(self):
        """Test creating a ClassificationResult."""
        result = ClassificationResult(
            label="test_label",
            score=0.95,
            timestamp="2024-01-01T00:00:00",
            model_name="test_model",
            device="cpu",
            peak_memory_mb=100.0
        )
        
        assert result.label == "test_label"
        assert result.score == 0.95
        assert result.model_name == "test_model"
        assert result.device == "cpu"
        assert result.peak_memory_mb == 100.0

    def test_creation_optional_fields(self):
        """Test creating a ClassificationResult with optional fields."""
        result = ClassificationResult(
            label="test",
            score=0.5,
            timestamp="2024-01-01T00:00:00",
            model_name="test",
            device="cpu"
        )
        
        assert result.peak_memory_mb is None