import pytest
import torch
import numpy as np
from pathlib import Path
import sys
from src.models.base_model import DistilBERTWrapper, load_distilbert_cpu


class TestDistilBERTWrapper:
    """Unit tests for the DistilBERTWrapper class."""

    def test_initialization(self):
        """Test that the wrapper initializes correctly."""
        wrapper = DistilBERTWrapper(model_name="distilbert-base-uncased")
        assert wrapper.model_name == "distilbert-base-uncased"
        assert wrapper.device.type == "cpu"
        assert wrapper.model is not None
        assert wrapper.tokenizer is not None
        assert wrapper.model.training is False  # Should be in eval mode

    def test_tokenize_single_string(self):
        """Test tokenization of a single string."""
        wrapper = DistilBERTWrapper()
        text = "Hello, world!"
        inputs = wrapper.tokenize(text)

        assert "input_ids" in inputs
        assert "attention_mask" in inputs
        assert isinstance(inputs["input_ids"], torch.Tensor)
        assert inputs["input_ids"].dim() == 2  # Batch dimension
        assert inputs["input_ids"].shape[0] == 1

    def test_tokenize_batch(self):
        """Test tokenization of a batch of strings."""
        wrapper = DistilBERTWrapper()
        texts = ["Hello, world!", "How are you?"]
        inputs = wrapper.tokenize(texts)

        assert "input_ids" in inputs
        assert "attention_mask" in inputs
        assert inputs["input_ids"].shape[0] == 2  # Batch size of 2

    def test_forward_pass(self):
        """Test that forward pass returns expected keys."""
        wrapper = DistilBERTWrapper()
        text = "Test forward pass."
        inputs = wrapper.tokenize(text)

        outputs = wrapper.forward(inputs["input_ids"], inputs["attention_mask"])

        assert "last_hidden_state" in outputs
        assert "hidden_states" in outputs
        assert "attention_mask" in outputs

        # Check dimensions
        assert outputs["last_hidden_state"].shape[0] == 1  # Batch size
        assert outputs["last_hidden_state"].shape[2] == 768  # Hidden size

    def test_get_activations(self):
        """Test extraction of activations from specific layers."""
        wrapper = DistilBERTWrapper()
        text = "Extract activations test."
        activations = wrapper.get_activations(text, layer_indices=[0, 2, 5])

        assert "layer_0" in activations
        assert "layer_2" in activations
        assert "layer_5" in activations

        # Check that activations are numpy arrays
        for key, value in activations.items():
            assert isinstance(value, np.ndarray)

    def test_get_activations_all_layers(self):
        """Test extraction of all layer activations."""
        wrapper = DistilBERTWrapper()
        text = "Get all activations."
        activations = wrapper.get_activations(text)

        # DistilBERT has 6 transformer layers
        assert len(activations) == 6
        assert "layer_0" in activations
        assert "layer_5" in activations


class TestLoadDistilbertCpu:
    """Tests for the load_distilbert_cpu convenience function."""

    def test_load_function_returns_wrapper(self):
        """Test that load_distilbert_cpu returns a DistilBERTWrapper instance."""
        wrapper = load_distilbert_cpu()
        assert isinstance(wrapper, DistilBERTWrapper)
        assert wrapper.device.type == "cpu"

    def test_load_with_custom_params(self):
        """Test loading with custom model name and max length."""
        wrapper = load_distilbert_cpu(model_name="distilbert-base-uncased", max_length=256)
        assert wrapper.max_length == 256
        assert wrapper.model_name == "distilbert-base-uncased"