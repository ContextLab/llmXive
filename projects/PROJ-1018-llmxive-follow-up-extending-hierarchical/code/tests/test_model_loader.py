import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from src.config import Config
from src.model_loader import (
    HiLSModelLoader,
    HiLSModelLoaderError,
    load_hils_checkpoint,
    validate_checkpoint
)


class TestModelLoader:
    """Tests for the HiLS model loader functionality."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration object."""
        config = MagicMock(spec=Config)
        config.model_path = "test/path/model"
        config.seed = 42
        config.chunk_size = 2048
        config.k_clusters = 100
        return config

    @pytest.fixture
    def mock_model(self):
        """Create a mock model object."""
        model = MagicMock(spec=AutoModelForCausalLM)
        model.config = MagicMock()
        model.config.model_type = "test-model"
        model.config.max_position_embeddings = 32768
        model.get_input_embeddings = MagicMock()
        model.eval = MagicMock()
        model.to = MagicMock(return_value=model)
        return model

    @pytest.fixture
    def mock_tokenizer(self):
        """Create a mock tokenizer object."""
        tokenizer = MagicMock(spec=AutoTokenizer)
        tokenizer.pad_token = "<pad>"
        tokenizer.pad_token_id = 0
        tokenizer.eos_token = "<eos>"
        tokenizer.__len__ = MagicMock(return_value=1000)
        return tokenizer

    def test_loader_initialization(self, mock_config):
        """Test that the loader initializes correctly."""
        loader = HiLSModelLoader(mock_config)
        assert loader.config == mock_config
        assert loader.model_path == "test/path/model"
        assert loader.model is None
        assert loader.tokenizer is None

    @patch('src.model_loader.AutoModelForCausalLM')
    @patch('src.model_loader.AutoTokenizer')
    def test_load_success(self, mock_tokenizer_class, mock_model_class, mock_config, mock_model, mock_tokenizer):
        """Test successful model loading."""
        mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer
        mock_model_class.from_pretrained.return_value = mock_model

        loader = HiLSModelLoader(mock_config)
        model, tokenizer = loader.load()

        assert model is not None
        assert tokenizer is not None
        assert loader.model is not None
        assert loader.tokenizer is not None
        mock_model_class.from_pretrained.assert_called_once()
        mock_tokenizer_class.from_pretrained.assert_called_once()

    @patch('src.model_loader.AutoModelForCausalLM')
    @patch('src.model_loader.AutoTokenizer')
    def test_load_sets_model_to_eval_mode(self, mock_tokenizer_class, mock_model_class, mock_config, mock_model, mock_tokenizer):
        """Test that load sets the model to eval mode."""
        mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer
        mock_model_class.from_pretrained.return_value = mock_model

        loader = HiLSModelLoader(mock_config)
        loader.load()

        mock_model.eval.assert_called_once()

    def test_validate_checkpoint_success(self, mock_model, mock_tokenizer):
        """Test successful checkpoint validation."""
        result = validate_checkpoint(mock_model, mock_tokenizer)
        assert result is True
        mock_model.eval.assert_called_once()

    def test_validate_checkpoint_model_none(self, mock_tokenizer):
        """Test validation fails when model is None."""
        with pytest.raises(HiLSModelLoaderError, match="Model or tokenizer is None."):
            validate_checkpoint(None, mock_tokenizer)

    def test_validate_checkpoint_tokenizer_none(self, mock_model):
        """Test validation fails when tokenizer is None."""
        with pytest.raises(HiLSModelLoaderError, match="Model or tokenizer is None."):
            validate_checkpoint(mock_model, None)

    def test_validate_checkpoint_missing_config(self, mock_tokenizer):
        """Test validation fails when model config is missing."""
        model_no_config = MagicMock()
        delattr(model_no_config, 'config')
        
        with pytest.raises(HiLSModelLoaderError, match="Model missing config."):
            validate_checkpoint(model_no_config, mock_tokenizer)

    def test_validate_checkpoint_missing_pad_token(self, mock_model):
        """Test validation fails when tokenizer pad_token_id is None."""
        tokenizer_no_pad = MagicMock()
        tokenizer_no_pad.pad_token_id = None
        
        with pytest.raises(HiLSModelLoaderError, match="Tokenizer pad_token_id is None."):
            validate_checkpoint(mock_model, tokenizer_no_pad)

    def test_load_hils_checkpoint(self, mock_config, mock_model, mock_tokenizer):
        """Test the convenience function load_hils_checkpoint."""
        with patch('src.model_loader.HiLSModelLoader') as MockLoader:
            mock_loader_instance = MagicMock()
            mock_loader_instance.load.return_value = (mock_model, mock_tokenizer)
            MockLoader.return_value = mock_loader_instance

            model, tokenizer = load_hils_checkpoint(mock_config)

            assert model is not None
            assert tokenizer is not None
            MockLoader.assert_called_once_with(mock_config)
            mock_loader_instance.load.assert_called_once()

    def test_load_raises_when_path_empty(self, mock_config):
        """Test that loading raises error when model path is empty."""
        mock_config.model_path = ""
        loader = HiLSModelLoader(mock_config)
        
        with pytest.raises(HiLSModelLoaderError, match="Model path is not specified"):
            loader.load()

    def test_load_raises_on_exception(self, mock_config):
        """Test that loading raises HiLSModelLoaderError on underlying exception."""
        with patch('src.model_loader.AutoTokenizer.from_pretrained') as mock_tk, \
             patch('src.model_loader.AutoModelForCausalLM.from_pretrained') as mock_md:
            
            mock_tk.side_effect = Exception("Connection failed")
            
            loader = HiLSModelLoader(mock_config)
            
            with pytest.raises(HiLSModelLoaderError, match="Failed to load HiLS model"):
                loader.load()
