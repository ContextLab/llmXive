"""
Tests for the model_loader utility.
"""

import gc
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import torch
from transformers import BitsAndBytesConfig

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.utils.model_loader import (
    get_4bit_quantization_config,
    load_model,
    get_model_card,
    validate_model_compatibility,
)


class TestModelLoader:
    """Test cases for model_loader.py"""

    def test_get_4bit_quantization_config(self):
        """Test that 4-bit quantization config is created correctly."""
        config = get_4bit_quantization_config()

        assert isinstance(config, BitsAndBytesConfig)
        assert config.load_in_4bit is True
        assert config.bnb_4bit_compute_dtype == torch.float16
        assert config.bnb_4bit_use_double_quant is True
        assert config.bnb_4bit_quant_type == "nf4"

    @patch("src.utils.model_loader.AutoTokenizer.from_pretrained")
    @patch("src.utils.model_loader.AutoModelForCausalLM.from_pretrained")
    def test_load_model_with_mock(self, mock_model, mock_tokenizer):
        """Test model loading with mocked dependencies."""
        # Setup mocks
        mock_tokenizer_instance = MagicMock()
        mock_tokenizer_instance.pad_token_id = None
        mock_tokenizer_instance.eos_token = "<eos>"
        mock_tokenizer.return_value = mock_tokenizer_instance

        mock_model_instance = MagicMock()
        mock_model_instance.requires_grad_ = MagicMock()
        mock_model_instance.eval = MagicMock()
        mock_model_instance.hf_device_map = {"": "cpu"}
        mock_model.return_value = mock_model_instance

        # Load model
        model, tokenizer = load_model("test-model", device_map="cpu")

        # Assertions
        mock_tokenizer.assert_called_once()
        mock_model.assert_called_once()
        mock_model_instance.requires_grad_.assert_called_once_with(False)
        mock_model_instance.eval.assert_called_once()
        assert tokenizer.pad_token == "<eos>"

    @patch("src.utils.model_loader.AutoConfig.from_pretrained")
    def test_get_model_card(self, mock_config):
        """Test retrieving model card information."""
        # Setup mock config
        mock_config_instance = MagicMock()
        mock_config_instance.model_type = "llama"
        mock_config_instance.vocab_size = 32000
        mock_config_instance.hidden_size = 4096
        mock_config_instance.num_attention_heads = 32
        mock_config_instance.num_hidden_layers = 32
        mock_config.return_value = mock_config_instance

        model_card = get_model_card("test-model")

        assert model_card["model_id"] == "test-model"
        assert model_card["model_type"] == "llama"
        assert model_card["vocab_size"] == 32000
        assert model_card["hidden_size"] == 4096

    @patch("src.utils.model_loader.get_model_card")
    def test_validate_model_compatibility_small(self, mock_card):
        """Test validation for a small model that fits in memory."""
        mock_card.return_value = {
            "model_id": "small-model",
            "hidden_size": 512,
            "num_attention_heads": 8,
            "num_hidden_layers": 4,
            "vocab_size": 1000,
        }

        is_compatible = validate_model_compatibility(
            "small-model",
            max_memory_gb=7.0,
            require_4bit=True,
        )

        assert is_compatible is True

    @patch("src.utils.model_loader.get_model_card")
    def test_validate_model_compatibility_large(self, mock_card):
        """Test validation for a large model that exceeds memory."""
        # Simulate a very large model
        mock_card.return_value = {
            "model_id": "huge-model",
            "hidden_size": 8192,
            "num_attention_heads": 64,
            "num_hidden_layers": 80,
            "vocab_size": 128000,
        }

        is_compatible = validate_model_compatibility(
            "huge-model",
            max_memory_gb=7.0,
            require_4bit=True,
        )

        # This should fail due to memory constraints
        assert is_compatible is False

    def test_validate_model_compatibility_error(self):
        """Test validation when model card retrieval fails."""
        with patch("src.utils.model_loader.get_model_card") as mock_card:
            mock_card.return_value = {"model_id": "error-model", "error": "Not found"}

            is_compatible = validate_model_compatibility("error-model")

            assert is_compatible is False

    @patch("src.utils.model_loader.AutoTokenizer.from_pretrained")
    @patch("src.utils.model_loader.AutoModelForCausalLM.from_pretrained")
    def test_load_model_sets_requires_grad_false(self, mock_model, mock_tokenizer):
        """Test that loaded model has requires_grad set to False."""
        mock_tokenizer_instance = MagicMock()
        mock_tokenizer_instance.pad_token_id = 1
        mock_tokenizer.return_value = mock_tokenizer_instance

        mock_model_instance = MagicMock()
        mock_model_instance.hf_device_map = {"": "cpu"}
        mock_model.return_value = mock_model_instance

        load_model("test-model", device_map="cpu")

        # Verify requires_grad_ was called with False
        mock_model_instance.requires_grad_.assert_called_once_with(False)

    @patch("src.utils.model_loader.AutoTokenizer.from_pretrained")
    @patch("src.utils.model_loader.AutoModelForCausalLM.from_pretrained")
    def test_load_model_sets_eval_mode(self, mock_model, mock_tokenizer):
        """Test that loaded model is set to eval mode."""
        mock_tokenizer_instance = MagicMock()
        mock_tokenizer_instance.pad_token_id = 1
        mock_tokenizer.return_value = mock_tokenizer_instance

        mock_model_instance = MagicMock()
        mock_model_instance.hf_device_map = {"": "cpu"}
        mock_model.return_value = mock_model_instance

        load_model("test-model", device_map="cpu")

        # Verify eval was called
        mock_model_instance.eval.assert_called_once()
