import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

import pytest
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

# Add the code root to the path so we can import src
code_root = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_root))

from src.utils.model_loader import (
    get_4bit_quantization_config,
    load_model,
    get_model_card,
    validate_model_compatibility,
    main
)
from src.utils.config import set_global_config, SocraticConfig

@pytest.fixture
def mock_config():
    """Fixture to set up a mock configuration."""
    config = SocraticConfig(
        BASE_MODEL_ID="hf-internal-testing/tiny-random-LlamaForCausalLM",
        CRITIC_MODEL_ID="hf-internal-testing/tiny-random-LlamaForCausalLM",
        SEED=42
    )
    set_global_config(config)
    return config

class TestQuantizationConfig:
    def test_get_4bit_quantization_config(self, mock_config):
        """Test that the 4-bit config is generated correctly."""
        config = get_4bit_quantization_config()
        assert isinstance(config, BitsAndBytesConfig)
        assert config.load_in_4bit is True
        assert config.bnb_4bit_quant_type == "nf4"

class TestModelLoading:
    @patch('src.utils.model_loader.AutoModelForCausalLM.from_pretrained')
    @patch('src.utils.model_loader.AutoTokenizer.from_pretrained')
    def test_load_model_mocked(self, mock_tokenizer, mock_model, mock_config):
        """Test load_model with mocked dependencies."""
        # Setup mocks
        mock_tokenizer_instance = MagicMock()
        mock_tokenizer_instance.pad_token = None
        mock_tokenizer.return_value = mock_tokenizer_instance
        
        mock_model_instance = MagicMock()
        mock_model_instance.num_parameters.return_value = 100
        mock_model.return_value = mock_model_instance
        
        # Call function
        model, tokenizer = load_model()
        
        # Assertions
        mock_tokenizer.assert_called_once()
        mock_model.assert_called_once()
        assert model == mock_model_instance
        assert tokenizer == mock_tokenizer_instance

    @patch('src.utils.model_loader.AutoModelForCausalLM.from_pretrained')
    @patch('src.utils.model_loader.AutoTokenizer.from_pretrained')
    def test_load_model_4bit_disabled(self, mock_tokenizer, mock_model, mock_config):
        """Test load_model with 4-bit disabled."""
        mock_tokenizer_instance = MagicMock()
        mock_tokenizer_instance.pad_token = None
        mock_tokenizer.return_value = mock_tokenizer_instance
        
        mock_model_instance = MagicMock()
        mock_model_instance.num_parameters.return_value = 100
        mock_model.return_value = mock_model_instance
        
        model, tokenizer = load_model(use_4bit=False)
        
        # Verify quantization_config was NOT passed
        call_kwargs = mock_model.call_args[1]
        assert 'quantization_config' not in call_kwargs

class TestModelUtilities:
    def test_get_model_card(self, mock_config):
        """Test get_model_card with a mock model."""
        mock_model = MagicMock()
        mock_model.config.model_type = "test_model"
        mock_model.config.hidden_size = 768
        
        card = get_model_card(mock_model)
        assert card is not None
        assert card["model_type"] == "test_model"
        assert card["hidden_size"] == 768

    def test_validate_model_compatibility(self, mock_config):
        """Test validate_model_compatibility."""
        # Valid model
        valid_model = MagicMock()
        valid_model.forward = lambda x: x
        valid_model.config = MagicMock()
        
        assert validate_model_compatibility(valid_model) is True
        
        # Invalid model (no forward)
        invalid_model = MagicMock(spec=[])
        assert validate_model_compatibility(invalid_model) is False
        
        # None model
        assert validate_model_compatibility(None) is False

class TestMain:
    @patch('src.utils.model_loader.load_model')
    @patch('src.utils.model_loader.validate_model_compatibility')
    @patch('src.utils.model_loader.get_model_card')
    @patch('src.utils.model_loader.sys.exit')
    def test_main_success(self, mock_exit, mock_card, mock_valid, mock_load, mock_config, capsys):
        """Test main function on success."""
        mock_load.return_value = (MagicMock(), MagicMock())
        mock_valid.return_value = True
        mock_card.return_value = {"test": "data"}
        
        main()
        
        mock_exit.assert_called_once_with(0)
        captured = capsys.readouterr()
        assert "Successfully loaded model" in captured.out

    @patch('src.utils.model_loader.load_model')
    @patch('src.utils.model_loader.validate_model_compatibility')
    @patch('src.utils.model_loader.sys.exit')
    def test_main_failure(self, mock_exit, mock_valid, mock_load, mock_config, capsys):
        """Test main function on failure."""
        mock_load.return_value = (MagicMock(), MagicMock())
        mock_valid.return_value = False
        
        main()
        
        mock_exit.assert_called_once_with(1)
        captured = capsys.readouterr()
        assert "failed compatibility check" in captured.out

    @patch('src.utils.model_loader.load_model')
    @patch('src.utils.model_loader.sys.exit')
    def test_main_exception(self, mock_exit, mock_load, mock_config, capsys):
        """Test main function when an exception occurs."""
        mock_load.side_effect = Exception("Test Error")
        
        main()
        
        mock_exit.assert_called_once_with(1)
        captured = capsys.readouterr()
        assert "Error during model loading" in captured.out