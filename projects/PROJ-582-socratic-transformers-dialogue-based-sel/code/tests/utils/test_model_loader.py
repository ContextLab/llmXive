"""
Tests for the Model Loader Utility (T007).
"""
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

# Ensure the project code path is available
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "projects" / "PROJ-582-socratic-transformers-dialogue-based-sel" / "code"))

from src.utils.model_loader import (
    load_model,
    get_model_card,
    validate_model_compatibility,
    _get_quantization_config,
)
from src.utils.config import set_global_config, SocraticConfig


@pytest.fixture
def mock_config_cpu():
    """Fixture to configure the environment for CPU/low-memory mode."""
    config = SocraticConfig(
        use_cpu=True,
        low_memory_mode=True,
        model_path="test-model",
        tokenizer_path="test-model",
    )
    set_global_config(config)
    return config


@pytest.fixture
def mock_config_gpu():
    """Fixture to configure the environment for standard GPU mode."""
    config = SocraticConfig(
        use_cpu=False,
        low_memory_mode=False,
        model_path="test-model",
        tokenizer_path="test-model",
    )
    set_global_config(config)
    return config


class TestQuantizationConfig:
    """Tests for the quantization configuration logic."""

    def test_get_quantization_config_cpu_mode(self, mock_config_cpu):
        """Verify that 4-bit config is returned when CPU/low-memory mode is active."""
        config = _get_quantization_config()
        assert config is not None
        assert config.load_in_4bit is True
        assert config.bnb_4bit_use_double_quant is True

    def test_get_quantization_config_gpu_mode(self, mock_config_gpu):
        """Verify that None is returned when not in constrained mode."""
        config = _get_quantization_config()
        assert config is None


class TestModelLoader:
    """Tests for the main loading functions."""

    @patch("src.utils.model_loader.AutoModelForCausalLM.from_pretrained")
    @patch("src.utils.model_loader.AutoTokenizer.from_pretrained")
    def test_load_model_with_quantization(
        self, mock_tokenizer, mock_model, mock_config_cpu
    ):
        """Test that load_model attempts to use BitsAndBytesConfig in CPU mode."""
        # Setup mocks
        mock_tokenizer.return_value = MagicMock(pad_token="</s>")
        mock_model.return_value = MagicMock(
            config=MagicMock(model_type="llama", architectures=["LlamaForCausalLM"]),
            device_map={"": "cpu"},
        )

        model, tokenizer = load_model("test-model")

        # Verify quantization config was passed
        call_kwargs = mock_model.call_args
        assert "quantization_config" in call_kwargs.kwargs
        assert isinstance(call_kwargs.kwargs["quantization_config"], BitsAndBytesConfig)

    @patch("src.utils.model_loader.AutoModelForCausalLM.from_pretrained")
    @patch("src.utils.model_loader.AutoTokenizer.from_pretrained")
    def test_load_model_without_quantization(
        self, mock_tokenizer, mock_model, mock_config_gpu
    ):
        """Test that load_model skips quantization in standard GPU mode."""
        mock_tokenizer.return_value = MagicMock(pad_token="</s>")
        mock_model.return_value = MagicMock(
            config=MagicMock(model_type="llama", architectures=["LlamaForCausalLM"]),
            device_map={"": "cuda:0"},
        )

        model, tokenizer = load_model("test-model")

        call_kwargs = mock_model.call_args
        assert "quantization_config" not in call_kwargs.kwargs or call_kwargs.kwargs.get("quantization_config") is None


class TestModelCard:
    """Tests for model metadata extraction."""

    def test_get_model_card_success(self):
        """Verify card extraction from a mock model."""
        mock_model = MagicMock()
        mock_model.config = MagicMock(
            model_type="llama",
            hidden_size=4096,
            num_attention_heads=32,
            num_hidden_layers=32,
            vocab_size=32000,
            architectures=["LlamaForCausalLM"],
        )
        
        card = get_model_card(mock_model)
        
        assert card["model_type"] == "llama"
        assert card["hidden_size"] == 4096
        assert card["vocab_size"] == 32000

    def test_get_model_card_no_config(self):
        """Verify graceful handling of models without config."""
        mock_model = MagicMock(spec=[])
        card = get_model_card(mock_model)
        assert "error" in card


class TestCompatibility:
    """Tests for model architecture validation."""

    def test_validate_compatibility_match(self):
        """Verify validation passes when architecture matches."""
        mock_model = MagicMock()
        mock_model.config = MagicMock(architectures=["LlamaForCausalLM"])
        
        assert validate_model_compatibility(mock_model, ["Llama"]) is True
        assert validate_model_compatibility(mock_model, ["LlamaForCausalLM"]) is True

    def test_validate_compatibility_no_match(self):
        """Verify validation fails when architecture does not match."""
        mock_model = MagicMock()
        mock_model.config = MagicMock(architectures=["GPT2LMHeadModel"])
        
        assert validate_model_compatibility(mock_model, ["Llama"]) is False

    def test_validate_compatibility_no_architectures(self):
        """Verify validation fails if architectures list is missing."""
        mock_model = MagicMock()
        mock_model.config = MagicMock(architectures=[])
        
        assert validate_model_compatibility(mock_model, ["Llama"]) is False
