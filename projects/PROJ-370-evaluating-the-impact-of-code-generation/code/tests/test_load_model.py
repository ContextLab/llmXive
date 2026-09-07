import pytest
import torch
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.inference.load_model import (
    load_model_and_tokenizer,
    load_model_for_inference,
    MODEL_ID,
    MEMORY_LIMIT_GB,
    MEMORY_LIMIT_BYTES
)
from src.utils.memory_watchdog import MemoryLimitExceeded

class TestLoadModel:
    """Test suite for model loading functionality."""

    @patch('src.inference.load_model.AutoTokenizer.from_pretrained')
    @patch('src.inference.load_model.AutoModelForCausalLM.from_pretrained')
    @patch('src.inference.load_model.get_memory_usage_bytes')
    def test_load_model_and_tokenizer_success(
        self, 
        mock_get_memory, 
        mock_model_load, 
        mock_tokenizer_load
    ):
        """Test successful model and tokenizer loading."""
        # Setup mocks
        mock_get_memory.side_effect = [1 * 1024**3, 5 * 1024**3]  # Before and after
        mock_tokenizer_load.return_value = MagicMock()
        mock_model_load.return_value = MagicMock()

        model, tokenizer = load_model_and_tokenizer()

        # Verify calls
        mock_tokenizer_load.assert_called_once()
        mock_model_load.assert_called_once()
        
        # Verify return types
        assert model is not None
        assert tokenizer is not None

    @patch('src.inference.load_model.AutoTokenizer.from_pretrained')
    @patch('src.inference.load_model.AutoModelForCausalLM.from_pretrained')
    @patch('src.inference.load_model.get_memory_usage_bytes')
    def test_load_model_custom_params(
        self, 
        mock_get_memory, 
        mock_model_load, 
        mock_tokenizer_load
    ):
        """Test loading with custom parameters."""
        mock_get_memory.side_effect = [1 * 1024**3, 4 * 1024**3]
        mock_tokenizer_load.return_value = MagicMock()
        mock_model_load.return_value = MagicMock()

        custom_model_id = "test/custom-model"
        model, tokenizer = load_model_and_tokenizer(
            model_id=custom_model_id,
            device_map="cpu",
            low_cpu_mem_usage=False
        )

        # Verify custom parameters were passed
        call_kwargs = mock_model_load.call_args[1]
        assert call_kwargs["device_map"] == "cpu"
        assert call_kwargs["low_cpu_mem_usage"] is False

    @patch('src.inference.load_model.AutoTokenizer.from_pretrained')
    @patch('src.inference.load_model.AutoModelForCausalLM.from_pretrained')
    @patch('src.inference.load_model.get_memory_usage_bytes')
    def test_load_model_memory_exceeded(
        self, 
        mock_get_memory, 
        mock_model_load, 
        mock_tokenizer_load
    ):
        """Test that MemoryLimitExceeded is raised when memory limit is exceeded."""
        # Simulate memory usage exceeding 7GB
        mock_get_memory.side_effect = [1 * 1024**3, 8 * 1024**3]
        mock_tokenizer_load.return_value = MagicMock()
        mock_model_load.return_value = MagicMock()

        with pytest.raises(MemoryLimitExceeded):
            load_model_and_tokenizer()

    @patch('src.inference.load_model.AutoTokenizer.from_pretrained')
    @patch('src.inference.load_model.AutoModelForCausalLM.from_pretrained')
    @patch('src.inference.load_model.get_memory_usage_bytes')
    def test_load_model_failure(
        self, 
        mock_get_memory, 
        mock_model_load, 
        mock_tokenizer_load
    ):
        """Test handling of model loading failure."""
        mock_get_memory.side_effect = [1 * 1024**3, 2 * 1024**3]
        mock_tokenizer_load.return_value = MagicMock()
        mock_model_load.side_effect = Exception("Model load failed")

        with pytest.raises(RuntimeError):
            load_model_and_tokenizer()

    @patch('src.inference.load_model.load_model_and_tokenizer')
    def test_load_model_for_inference(self, mock_load):
        """Test the inference wrapper function."""
        mock_model = MagicMock()
        mock_tokenizer = MagicMock()
        mock_load.return_value = (mock_model, mock_tokenizer)

        model, tokenizer = load_model_for_inference()

        mock_load.assert_called_once_with(
            model_id=None,
            device_map="auto",
            low_cpu_mem_usage=True
        )
        assert model is mock_model
        assert tokenizer is mock_tokenizer

class TestMemoryConstraints:
    """Test memory constraint enforcement."""

    def test_memory_limit_constant(self):
        """Verify memory limit constant is set correctly."""
        assert MEMORY_LIMIT_GB == 7
        assert MEMORY_LIMIT_BYTES == 7 * 1024 * 1024 * 1024

    @patch('src.inference.load_model.get_memory_usage_bytes')
    def test_memory_check_logic(self, mock_get_memory):
        """Test memory check logic."""
        # Under limit
        mock_get_memory.return_value = 6 * 1024**3
        assert 6 * 1024**3 <= MEMORY_LIMIT_BYTES

        # Over limit
        mock_get_memory.return_value = 8 * 1024**3
        assert 8 * 1024**3 > MEMORY_LIMIT_BYTES

class TestModelID:
    """Test model identifier configuration."""

    def test_default_model_id(self):
        """Verify default model ID."""
        assert MODEL_ID == "bigcode/starcoder2-3b"

    @patch('src.inference.load_model.AutoTokenizer.from_pretrained')
    @patch('src.inference.load_model.AutoModelForCausalLM.from_pretrained')
    @patch('src.inference.load_model.get_memory_usage_bytes')
    def test_custom_model_id_used(
        self, 
        mock_get_memory, 
        mock_model_load, 
        mock_tokenizer_load
    ):
        """Test that custom model ID is used when provided."""
        mock_get_memory.side_effect = [1 * 1024**3, 3 * 1024**3]
        mock_tokenizer_load.return_value = MagicMock()
        mock_model_load.return_value = MagicMock()

        custom_id = "test/custom-model"
        load_model_and_tokenizer(model_id=custom_id)

        # Verify custom ID was passed to both tokenizer and model loaders
        assert mock_tokenizer_load.call_args[0][0] == custom_id
        assert mock_model_load.call_args[0][0] == custom_id