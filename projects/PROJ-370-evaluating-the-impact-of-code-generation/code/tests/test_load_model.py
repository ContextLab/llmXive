"""
Tests for model loading functionality.
"""

import pytest
import torch
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.inference.load_model import (
    load_model_and_tokenizer,
    load_model_for_inference,
    MODEL_ID,
    MEMORY_LIMIT_GB,
)


class TestLoadModel:
    """Test cases for model loading functions."""

    @patch('src.inference.load_model.AutoModelForCausalLM.from_pretrained')
    @patch('src.inference.load_model.AutoTokenizer.from_pretrained')
    def test_load_model_mocked(self, mock_tokenizer, mock_model):
        """Test model loading with mocked dependencies."""
        # Setup mocks
        mock_model_instance = MagicMock()
        mock_model_instance.parameters.return_value = [MagicMock()]
        mock_model_instance.parameters.return_value[0].device = "cpu"
        mock_model_instance.dtype = torch.float16
        mock_model.return_value = mock_model_instance

        mock_tokenizer_instance = MagicMock()
        mock_tokenizer.return_value = mock_tokenizer_instance

        # Call function
        model, tokenizer = load_model_and_tokenizer(
            model_id="test/model",
            device_map="cpu",
            low_cpu_mem_usage=True,
            torch_dtype=torch.float16,
        )

        # Verify calls
        mock_tokenizer.assert_called_once()
        mock_model.assert_called_once()

        # Verify return types
        assert model is not None
        assert tokenizer is not None

    @patch('src.inference.load_model.AutoModelForCausalLM.from_pretrained')
    @patch('src.inference.load_model.AutoTokenizer.from_pretrained')
    def test_load_model_with_float16(self, mock_tokenizer, mock_model):
        """Test that float16 precision is used when requested."""
        # Setup mocks
        mock_model_instance = MagicMock()
        mock_model_instance.parameters.return_value = [MagicMock()]
        mock_model_instance.dtype = torch.float16
        mock_model.return_value = mock_model_instance

        mock_tokenizer_instance = MagicMock()
        mock_tokenizer.return_value = mock_tokenizer_instance

        # Call function with float16
        model, tokenizer = load_model_for_inference(use_float16=True)

        # Verify float16 was used
        call_kwargs = mock_model.call_args[1]
        assert call_kwargs['torch_dtype'] == torch.float16

    @patch('src.inference.load_model.AutoModelForCausalLM.from_pretrained')
    @patch('src.inference.load_model.AutoTokenizer.from_pretrained')
    def test_load_model_with_float32(self, mock_tokenizer, mock_model):
        """Test that float32 precision is used when requested."""
        # Setup mocks
        mock_model_instance = MagicMock()
        mock_model_instance.dtype = torch.float32
        mock_model.return_value = mock_model_instance

        mock_tokenizer_instance = MagicMock()
        mock_tokenizer.return_value = mock_tokenizer_instance

        # Call function with float32
        model, tokenizer = load_model_for_inference(use_float16=False)

        # Verify float32 was used
        call_kwargs = mock_model.call_args[1]
        assert call_kwargs['torch_dtype'] == torch.float32

    def test_invalid_device_map(self):
        """Test that invalid device_map raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported device_map"):
            load_model_and_tokenizer(
                model_id="test/model",
                device_map="invalid_device",
            )

    @patch('src.inference.load_model.AutoModelForCausalLM.from_pretrained')
    @patch('src.inference.load_model.AutoTokenizer.from_pretrained')
    def test_model_loading_failure(self, mock_tokenizer, mock_model):
        """Test that model loading failure raises RuntimeError."""
        mock_model.side_effect = Exception("Model loading failed")

        with pytest.raises(RuntimeError, match="Model loading failed"):
            load_model_and_tokenizer(model_id="test/model")

    @patch('src.inference.load_model.AutoModelForCausalLM.from_pretrained')
    @patch('src.inference.load_model.AutoTokenizer.from_pretrained')
    def test_default_parameters(self, mock_tokenizer, mock_model):
        """Test that default parameters are used when not specified."""
        # Setup mocks
        mock_model_instance = MagicMock()
        mock_model_instance.dtype = torch.float16
        mock_model.return_value = mock_model_instance

        mock_tokenizer_instance = MagicMock()
        mock_tokenizer.return_value = mock_tokenizer_instance

        # Call with defaults
        model, tokenizer = load_model_for_inference()

        # Verify default parameters were used
        call_kwargs = mock_model.call_args[1]
        assert call_kwargs['device_map'] == "auto"
        assert call_kwargs['low_cpu_mem_usage'] is True
        assert call_kwargs['torch_dtype'] == torch.float16


class TestMemoryConstraints:
    """Test cases for memory constraint functionality."""

    def test_memory_limit_constant(self):
        """Test that memory limit constant is set correctly."""
        assert MEMORY_LIMIT_GB == 7.0

    @patch('src.inference.load_model.AutoModelForCausalLM.from_pretrained')
    @patch('src.inference.load_model.AutoTokenizer.from_pretrained')
    def test_max_memory_calculation(self, mock_tokenizer, mock_model):
        """Test that max memory is calculated based on limit."""
        # Setup mocks
        mock_model_instance = MagicMock()
        mock_model_instance.dtype = torch.float16
        mock_model.return_value = mock_model_instance

        mock_tokenizer_instance = MagicMock()
        mock_tokenizer.return_value = mock_tokenizer_instance

        # Call without explicit max_memory
        load_model_and_tokenizer(model_id="test/model")

        # Verify max_memory was set (should be ~6.3GB which is 90% of 7GB)
        call_kwargs = mock_model.call_args[1]
        assert 'max_memory' in call_kwargs
        # Check that the value is a dictionary with device keys
        assert isinstance(call_kwargs['max_memory'], dict)


class TestModelID:
    """Test cases for model identification."""

    def test_default_model_id(self):
        """Test that default model ID is correct."""
        assert MODEL_ID == "bigcode/starcoder2-3b"

    @patch('src.inference.load_model.AutoModelForCausalLM.from_pretrained')
    @patch('src.inference.load_model.AutoTokenizer.from_pretrained')
    def test_custom_model_id(self, mock_tokenizer, mock_model):
        """Test that custom model ID can be used."""
        # Setup mocks
        mock_model_instance = MagicMock()
        mock_model_instance.dtype = torch.float16
        mock_model.return_value = mock_model_instance

        mock_tokenizer_instance = MagicMock()
        mock_tokenizer.return_value = mock_tokenizer_instance

        custom_model_id = "custom/model"
        load_model_and_tokenizer(model_id=custom_model_id)

        # Verify custom model ID was used
        call_args = mock_tokenizer.call_args[0][0]
        assert call_args == custom_model_id

        call_args = mock_model.call_args[0][0]
        assert call_args == custom_model_id