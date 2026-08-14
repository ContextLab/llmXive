"""
Contract tests for the model loader utility (T007).

These tests verify that the model loader correctly configures 4-bit quantization
and attempts to load models as specified in the project configuration.
"""

import pytest
from unittest.mock import patch, MagicMock

from src.utils.config import get_config
from src.utils.model_loader import (
    get_4bit_quantization_config,
    load_model,
    validate_model_compatibility,
    get_model_card,
)


class TestQuantizationConfig:
    """Tests for the 4-bit quantization configuration factory."""

    def test_returns_bitsandbytes_config(self):
        """Assert that get_4bit_quantization_config returns a BitsAndBytesConfig."""
        from transformers import BitsAndBytesConfig

        config = get_4bit_quantization_config()
        assert isinstance(config, BitsAndBytesConfig)

    def test_load_in_4bit_enabled(self):
        """Assert that load_in_4bit is True."""
        config = get_4bit_quantization_config()
        assert config.load_in_4bit is True

    def test_compute_dtype(self):
        """Assert that compute dtype is set to float32 for CPU compatibility."""
        import torch

        config = get_4bit_quantization_config()
        assert config.bnb_4bit_compute_dtype == torch.float32


class TestModelLoader:
    """Tests for the load_model function."""

    @patch("src.utils.model_loader.AutoTokenizer.from_pretrained")
    @patch("src.utils.model_loader.AutoModelForCausalLM.from_pretrained")
    def test_load_model_uses_config_if_not_provided(
        self, mock_model_from_pretrained, mock_tokenizer_from_pretrained
    ):
        """Assert that load_model uses BASE_MODEL_ID from config when model_id is None."""
        mock_config = MagicMock()
        mock_config.BASE_MODEL_ID = "test/mock-model-id"
        mock_tokenizer = MagicMock()
        mock_model = MagicMock()
        mock_model.config.model_type = "test_model"
        mock_model.num_parameters.return_value = 1000

        mock_tokenizer_from_pretrained.return_value = mock_tokenizer
        mock_model_from_pretrained.return_value = mock_model

        # Patch get_config to return our mock
        with patch("src.utils.model_loader.get_config", return_value=mock_config):
            model, tokenizer = load_model()

        # Verify from_pretrained was called with the config ID
        mock_model_from_pretrained.assert_called_once()
        call_args = mock_model_from_pretrained.call_args
        assert call_args[0][0] == "test/mock-model-id"

    def test_load_model_raises_on_missing_id(self):
        """Assert that load_model raises ValueError if no model ID is found."""
        mock_config = MagicMock()
        mock_config.BASE_MODEL_ID = None

        with patch("src.utils.model_loader.get_config", return_value=mock_config):
            with pytest.raises(ValueError, match="Model ID not provided"):
                load_model()

    @patch("src.utils.model_loader.AutoTokenizer.from_pretrained")
    @patch("src.utils.model_loader.AutoModelForCausalLM.from_pretrained")
    def test_load_model_applies_quantization(
        self, mock_model_from_pretrained, mock_tokenizer_from_pretrained
    ):
        """Assert that the quantization config is passed to the model loader."""
        from transformers import BitsAndBytesConfig

        mock_config = MagicMock()
        mock_config.BASE_MODEL_ID = "test/mock-model-id"
        mock_tokenizer = MagicMock()
        mock_model = MagicMock()
        mock_model.config.model_type = "test_model"
        mock_model.num_parameters.return_value = 1000

        mock_tokenizer_from_pretrained.return_value = mock_tokenizer
        mock_model_from_pretrained.return_value = mock_model

        with patch("src.utils.model_loader.get_config", return_value=mock_config):
            model, tokenizer = load_model()

        # Verify quantization_config was passed
        call_kwargs = mock_model_from_pretrained.call_args[1]
        assert "quantization_config" in call_kwargs
        assert isinstance(call_kwargs["quantization_config"], BitsAndBytesConfig)


class TestModelValidation:
    """Tests for validation utilities."""

    def test_validate_model_compatibility(self):
        """Assert that validation returns True if features exist."""
        mock_model = MagicMock()
        mock_model.config.hidden_size = 768
        mock_model.config.num_attention_heads = 12

        assert validate_model_compatibility(mock_model, ["hidden_size"]) is True
        assert validate_model_compatibility(mock_model, ["hidden_size", "num_attention_heads"]) is True

    def test_validate_model_compatibility_missing_feature(self):
        """Assert that validation returns False if a feature is missing."""
        mock_model = MagicMock()
        mock_model.config.hidden_size = 768

        assert validate_model_compatibility(mock_model, ["non_existent_feature"]) is False

    def test_get_model_card(self):
        """Assert that get_model_card extracts correct metadata."""
        mock_model = MagicMock()
        mock_model.config.model_type = "gpt2"
        mock_model.config.vocab_size = 50257
        mock_model.config.hidden_size = 768
        mock_model.config.num_attention_heads = 12
        mock_model.config.num_hidden_layers = 12

        card = get_model_card(mock_model)

        assert card["model_type"] == "gpt2"
        assert card["vocab_size"] == 50257
        assert card["hidden_size"] == 768
        assert card["num_attention_heads"] == 12
        assert card["num_hidden_layers"] == 12
