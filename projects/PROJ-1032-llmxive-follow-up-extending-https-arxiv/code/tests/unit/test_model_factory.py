import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Ensure the src directory is in the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from llmxive.model_factory import load_model, SUPPORTED_MODELS, ERR_CPU_LOAD_FAIL
from llmxive.exceptions import ERR_CPU_LOAD_FAIL as ERR_CLASS

class TestModelFactory:
    """Tests for the model factory loading logic."""

    @patch('llmxive.model_factory.AutoTokenizer.from_pretrained')
    @patch('llmxive.model_factory.AutoModelForCausalLM.from_pretrained')
    def test_load_phi2_success(self, mock_model_load, mock_tokenizer_load):
        """Test successful loading of Phi-2."""
        mock_model = MagicMock()
        mock_tokenizer = MagicMock()
        mock_tokenizer.pad_token = None
        mock_tokenizer.eos_token = ""
        
        mock_model_load.return_value = mock_model
        mock_tokenizer_load.return_value = mock_tokenizer

        model, tokenizer = load_model("phi-2")

        assert model is mock_model
        assert tokenizer is mock_tokenizer
        mock_model_load.assert_called_once()
        # Verify 8-bit config was passed
        call_kwargs = mock_model_load.call_args[1]
        assert 'quantization_config' in call_kwargs

    @patch('llmxive.model_factory.AutoTokenizer.from_pretrained')
    @patch('llmxive.model_factory.AutoModelForCausalLM.from_pretrained')
    def test_load_qwen_success(self, mock_model_load, mock_tokenizer_load):
        """Test successful loading of Qwen1.5-1.8B."""
        mock_model = MagicMock()
        mock_tokenizer = MagicMock()
        mock_tokenizer.pad_token = None
        mock_tokenizer.eos_token = ""

        mock_model_load.return_value = mock_model
        mock_tokenizer_load.return_value = mock_tokenizer

        model, tokenizer = load_model("qwen1.5-1.8b")

        assert model is mock_model
        assert tokenizer is mock_tokenizer

    def test_load_invalid_model_id(self):
        """Test that invalid model ID raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported model_id"):
            load_model("invalid-model")

    def test_load_non_cpu_device(self):
        """Test that non-CPU device raises ValueError."""
        with pytest.raises(ValueError, match="only supports CPU"):
            load_model("phi-2", device="cuda")

    @patch('llmxive.model_factory.AutoModelForCausalLM.from_pretrained')
    def test_load_oom_raises_custom_exception(self, mock_model_load):
        """Test that OOM errors raise ERR_CPU_LOAD_FAIL."""
        mock_model_load.side_effect = RuntimeError("CUDA out of memory. Tried to allocate...")

        with pytest.raises(ERR_CPU_LOAD_FAIL, match="OOM"):
            load_model("phi-2")

    @patch('llmxive.model_factory.AutoModelForCausalLM.from_pretrained')
    def test_load_generic_error_raises_custom_exception(self, mock_model_load):
        """Test that generic load errors raise ERR_CPU_LOAD_FAIL."""
        mock_model_load.side_effect = OSError("File not found")

        with pytest.raises(ERR_CPU_LOAD_FAIL, match="Failed to load"):
            load_model("phi-2")

    @patch('llmxive.model_factory.AutoModelForCausalLM.from_pretrained')
    def test_load_memory_error_raises_custom_exception(self, mock_model_load):
        """Test that MemoryError raises ERR_CPU_LOAD_FAIL."""
        mock_model_load.side_effect = MemoryError("Out of memory")

        with pytest.raises(ERR_CPU_LOAD_FAIL, match="OOM"):
            load_model("phi-2")