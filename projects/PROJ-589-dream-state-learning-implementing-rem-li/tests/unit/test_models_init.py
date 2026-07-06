"""
Unit tests for code/models/__init__.py

Verifies that model loading functions work correctly with CPU optimization
and return expected types.
"""
import pytest
import torch
from transformers import AutoModel, AutoTokenizer

# Import the module under test
from code.models import load_model, get_model_config, DEFAULT_MODEL_NAME, DEFAULT_PRECISION, DEVICE


class TestModelLoader:
    """Tests for the model loading functionality."""

    def test_load_model_returns_tuple(self):
        """Test that load_model returns a tuple of (model, tokenizer)."""
        # Use a tiny model for fast unit testing
        model_name = "distilbert-base-uncased"
        model, tokenizer = load_model(model_name, device="cpu")
        
        assert isinstance(model, torch.nn.Module)
        assert isinstance(tokenizer, AutoTokenizer)

    def test_load_model_on_cpu(self):
        """Test that model is loaded on CPU device."""
        model_name = "distilbert-base-uncased"
        model, _ = load_model(model_name, device="cpu")
        
        # Check device placement
        for param in model.parameters():
            assert param.device.type == "cpu"
            break  # Only need to check one parameter

    def test_load_model_precision(self):
        """Test that model uses default float32 precision."""
        model_name = "distilbert-base-uncased"
        model, _ = load_model(model_name, device="cpu")
        
        # Check dtype of at least one parameter
        for param in model.parameters():
            assert param.dtype == DEFAULT_PRECISION
            break

    def test_load_model_eval_mode(self):
        """Test that model is set to evaluation mode by default."""
        model_name = "distilbert-base-uncased"
        model, _ = load_model(model_name, device="cpu")
        
        assert model.training is False

    def test_get_model_config(self):
        """Test that get_model_config returns valid configuration dict."""
        model_name = "distilbert-base-uncased"
        config = get_model_config(model_name)
        
        assert isinstance(config, dict)
        assert "model_type" in config
        assert "hidden_size" in config
        assert "num_attention_heads" in config
        assert "num_hidden_layers" in config
        assert "vocab_size" in config

    def test_get_model_config_invalid_model(self):
        """Test that get_model_config raises RuntimeError for invalid model."""
        with pytest.raises(RuntimeError, match="Failed to load config"):
            get_model_config("non-existent-model-12345")


class TestConstants:
    """Tests for module constants."""

    def test_default_model_name(self):
        """Test that default model name is a valid DistilBERT model."""
        assert "distilbert" in DEFAULT_MODEL_NAME.lower()

    def test_default_precision(self):
        """Test that default precision is float32."""
        assert DEFAULT_PRECISION == torch.float30
        assert DEFAULT_PRECISION == torch.float32

    def test_default_device(self):
        """Test that default device is CPU."""
        assert DEVICE == "cpu"
