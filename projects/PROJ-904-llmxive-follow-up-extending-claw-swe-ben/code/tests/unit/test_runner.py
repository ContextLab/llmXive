"""
Unit tests for the ModelRunner class.
"""

import pytest
import sys
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from models.runner import ModelRunner, GenerationConfig
from utils.logger import ModelExecutionError


class TestModelRunner:
    """Tests for the ModelRunner class."""

    def test_initialization(self):
        """Test that ModelRunner initializes correctly."""
        runner = ModelRunner(
            model_path="test-model",
            quantization_level="q4_k_m",
            device="cpu"
        )

        assert runner.model_path == "test-model"
        assert runner.quantization_level == "q4_k_m"
        assert runner.device == "cpu"
        assert runner._loaded is False
        assert runner.model is None
        assert runner.tokenizer is None

    def test_initialization_with_defaults(self):
        """Test ModelRunner initialization with default parameters."""
        runner = ModelRunner(model_path="test-model")

        assert runner.quantization_level == "q4_k_m"
        assert runner.device == "cpu"
        assert runner.max_memory_mb is None
        assert runner.timeout_seconds is None

    def test_initialization_with_memory_limit(self):
        """Test ModelRunner initialization with memory limit."""
        runner = ModelRunner(
            model_path="test-model",
            max_memory_mb=4096,
            timeout_seconds=30
        )

        assert runner.max_memory_mb == 4096
        assert runner.timeout_seconds == 30

    def test_generation_config_defaults(self):
        """Test GenerationConfig default values."""
        config = GenerationConfig()

        assert config.max_new_tokens == 256
        assert config.temperature == 0.7
        assert config.top_p == 0.9
        assert config.top_k == 50
        assert config.do_sample is True
        assert config.repetition_penalty == 1.1

    def test_generation_config_custom(self):
        """Test GenerationConfig with custom values."""
        config = GenerationConfig(
            max_new_tokens=512,
            temperature=0.9,
            top_p=0.95
        )

        assert config.max_new_tokens == 512
        assert config.temperature == 0.9
        assert config.top_p == 0.95

    @patch('models.runner.AutoTokenizer.from_pretrained')
    @patch('models.runner.AutoModelForCausalLM.from_pretrained')
    def test_load_model_success(self, mock_model, mock_tokenizer):
        """Test successful model loading."""
        # Setup mocks
        mock_tokenizer_instance = MagicMock()
        mock_tokenizer_instance.pad_token_id = None
        mock_tokenizer_instance.eos_token_id = 0
        mock_tokenizer.return_value = mock_tokenizer_instance

        mock_model_instance = MagicMock()
        mock_model.return_value = mock_model_instance

        runner = ModelRunner(model_path="test-model")
        result = runner.load_model()

        assert result is True
        assert runner._loaded is True
        assert runner.model is not None
        assert runner.tokenizer is not None
        mock_tokenizer.assert_called_once()
        mock_model.assert_called_once()

    @patch('models.runner.AutoTokenizer.from_pretrained')
    def test_load_model_tokenizer_failure(self, mock_tokenizer):
        """Test model loading fails when tokenizer loading fails."""
        mock_tokenizer.side_effect = Exception("Tokenizer load error")

        runner = ModelRunner(model_path="test-model")

        with pytest.raises(ModelExecutionError):
            runner.load_model()

    @patch('models.runner.AutoModelForCausalLM.from_pretrained')
    def test_load_model_model_failure(self, mock_model):
        """Test model loading fails when model loading fails."""
        # Setup tokenizer mock
        mock_tokenizer_instance = MagicMock()
        mock_tokenizer_instance.pad_token_id = None
        mock_tokenizer_instance.eos_token_id = 0

        with patch('models.runner.AutoTokenizer.from_pretrained', return_value=mock_tokenizer_instance):
            mock_model.side_effect = Exception("Model load error")

            runner = ModelRunner(model_path="test-model")

            with pytest.raises(ModelExecutionError):
                runner.load_model()

    @patch('models.runner.AutoTokenizer.from_pretrained')
    @patch('models.runner.AutoModelForCausalLM.from_pretrained')
    def test_unload_model(self, mock_model, mock_tokenizer):
        """Test model unloading."""
        # Setup mocks
        mock_tokenizer_instance = MagicMock()
        mock_tokenizer_instance.pad_token_id = None
        mock_tokenizer_instance.eos_token_id = 0
        mock_tokenizer.return_value = mock_tokenizer_instance

        mock_model_instance = MagicMock()
        mock_model.return_value = mock_model_instance

        runner = ModelRunner(model_path="test-model")
        runner.load_model()

        assert runner._loaded is True
        assert runner.model is not None

        runner.unload_model()

        assert runner._loaded is False
        assert runner.model is None
        assert runner.tokenizer is None

    def test_context_manager(self):
        """Test context manager functionality."""
        with patch.object(ModelRunner, 'load_model') as mock_load:
            with patch.object(ModelRunner, 'unload_model') as mock_unload:
                with ModelRunner(model_path="test-model") as runner:
                    mock_load.assert_called_once()
                    assert runner is not None

                mock_unload.assert_called_once()

    def test_get_quantization_config_none(self):
        """Test getting None quantization config."""
        runner = ModelRunner(model_path="test-model", quantization_level="none")
        config = runner._get_quantization_config()
        assert config is None

    def test_get_quantization_config_invalid(self):
        """Test getting invalid quantization config raises error."""
        runner = ModelRunner(model_path="test-model", quantization_level="invalid")
        with pytest.raises(ValueError):
            runner._get_quantization_config()

    def test_handle_memory_pressure_already_q4(self):
        """Test memory pressure handling when already at max quantization."""
        runner = ModelRunner(model_path="test-model", quantization_level="q4_k_m")
        result = runner._handle_memory_pressure()
        assert result is False

    @patch.object(ModelRunner, 'unload_model')
    @patch.object(ModelRunner, 'load_model')
    def test_handle_memory_pressure_downgrade_success(self, mock_load, mock_unload):
        """Test successful memory pressure handling via downgrade."""
        runner = ModelRunner(model_path="test-model", quantization_level="q8_0")
        result = runner._handle_memory_pressure()
        assert result is True
        assert runner.quantization_level == "q4_k_m"
        mock_unload.assert_called_once()
        mock_load.assert_called_once()
