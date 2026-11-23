"""
Unit tests for the DistilBERTWrapper model.
"""

import pytest
import torch
import numpy as np
from pathlib import Path
import sys

# Ensure the code directory is in the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.models.base_model import DistilBERTWrapper, load_distilbert_cpu


class TestDistilBERTWrapper:
    """Tests for the DistilBERTWrapper class."""

    @pytest.fixture
    def wrapper(self):
        """Create a DistilBERTWrapper instance for testing."""
        return DistilBERTWrapper(
            model_name="distilbert-base-uncased",
            cache_dir=None
        )

    def test_wrapper_initialization(self, wrapper):
        """Test that the wrapper initializes correctly."""
        assert wrapper.device.type == "cpu"
        assert wrapper.model is not None
        assert wrapper.tokenizer is not None
        assert wrapper.model_name == "distilbert-base-uncased"

    def test_device_is_cpu(self, wrapper):
        """Verify all model parameters are on CPU."""
        for param in wrapper.model.parameters():
            assert param.device.type == "cpu"

    def test_tokenization_single_text(self, wrapper):
        """Test tokenization of a single text."""
        text = "This is a test sentence."
        tokens = wrapper.tokenize(text)

        assert "input_ids" in tokens
        assert "attention_mask" in tokens
        assert tokens["input_ids"].shape[0] == 1
        assert isinstance(tokens["input_ids"], torch.Tensor)

    def test_tokenization_batch(self, wrapper):
        """Test tokenization of a batch of texts."""
        texts = ["First sentence.", "Second sentence.", "Third sentence."]
        tokens = wrapper.tokenize(texts)

        assert tokens["input_ids"].shape[0] == len(texts)
        assert "attention_mask" in tokens

    def test_forward_pass(self, wrapper):
        """Test a basic forward pass."""
        text = "This is a test."
        tokens = wrapper.tokenize(text)

        outputs = wrapper.forward(
            input_ids=tokens["input_ids"],
            attention_mask=tokens["attention_mask"]
        )

        assert outputs is not None
        assert hasattr(outputs, "last_hidden_state")
        assert outputs.last_hidden_state is not None

    def test_hidden_states_extraction(self, wrapper):
        """Test extraction of hidden states."""
        text = "Test extraction of hidden states."
        tokens = wrapper.tokenize(text)

        hidden_states = wrapper.get_hidden_states(
            input_ids=tokens["input_ids"],
            attention_mask=tokens["attention_mask"]
        )

        # DistilBERT has 6 transformer layers + embeddings
        assert len(hidden_states) == 7  # 6 layers + initial embeddings
        for state in hidden_states:
            assert isinstance(state, torch.Tensor)

    def test_layer_activations(self, wrapper):
        """Test extraction of specific layer activations."""
        text = "Test specific layer activations."
        tokens = wrapper.tokenize(text)

        activations = wrapper.get_layer_activations(
            input_ids=tokens["input_ids"],
            attention_mask=tokens["attention_mask"],
            layer_indices=[0, 2, 5]
        )

        assert len(activations) == 3
        assert 0 in activations
        assert 2 in activations
        assert 5 in activations

    def test_encode_single_text(self, wrapper):
        """Test encoding of a single text to embedding."""
        text = "This is a test for encoding."
        embeddings = wrapper.encode(text)

        assert isinstance(embeddings, np.ndarray)
        assert embeddings.shape[0] == 1
        assert embeddings.shape[1] == 768  # DistilBERT embedding size

    def test_encode_batch(self, wrapper):
        """Test encoding of a batch of texts."""
        texts = [
            "First text for encoding.",
            "Second text for encoding.",
            "Third text for encoding."
        ]
        embeddings = wrapper.encode(texts)

        assert isinstance(embeddings, np.ndarray)
        assert embeddings.shape[0] == len(texts)
        assert embeddings.shape[1] == 768

    def test_no_gradients(self, wrapper):
        """Verify that gradients are disabled for inference."""
        for param in wrapper.model.parameters():
            assert not param.requires_grad

    def test_repr(self, wrapper):
        """Test string representation of the wrapper."""
        repr_str = repr(wrapper)
        assert "DistilBERTWrapper" in repr_str
        assert "distilbert-base-uncased" in repr_str
        assert "cpu" in repr_str


class TestLoadDistilbertCpu:
    """Tests for the load_distilbert_cpu convenience function."""

    def test_load_function(self):
        """Test that the load function returns a wrapper."""
        wrapper = load_distilbert_cpu()

        assert isinstance(wrapper, DistilBERTWrapper)
        assert wrapper.device.type == "cpu"

    def test_load_with_custom_name(self):
        """Test loading with a custom model name."""
        wrapper = load_distilbert_cpu(model_name="distilbert-base-uncased")

        assert isinstance(wrapper, DistilBERTWrapper)
        assert wrapper.model_name == "distilbert-base-uncased"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])