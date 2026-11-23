"""
Unit tests for the model_loader utility.
"""

import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.utils.model_loader import (
    get_4bit_quantization_config,
    load_model,
    get_model_card,
    validate_model_compatibility,
)

class TestModelLoader:

    @patch("src.utils.model_loader.get_config")
    def test_get_4bit_quantization_config(self, mock_get_config):
        """Test that the quantization config is generated correctly."""
        config = get_4bit_quantization_config()
        assert config.load_in_4bit is True
        assert config.bnb_4bit_quant_type == "nf4"
        assert config.bnb_4bit_use_double_quant is True

    @patch("src.utils.model_loader.AutoTokenizer.from_pretrained")
    @patch("src.utils.model_loader.AutoModelForCausalLM.from_pretrained")
    @patch("src.utils.model_loader.get_config")
    def test_load_model_success(
        self, mock_config, mock_model_load, mock_tokenizer_load
    ):
        """Test successful model loading with mocked dependencies."""
        # Setup mocks
        mock_config.return_value.BASE_MODEL_ID = "test-model-id"
        mock_tokenizer_load.return_value = MagicMock(pad_token="</s>", eos_token="</s>")
        mock_model_load.return_value = MagicMock(hf_device_map={"": "cpu"})

        model, tokenizer = load_model()

        assert model is not None
        assert tokenizer is not None
        mock_model_load.assert_called_once()

    @patch("src.utils.model_loader.get_config")
    def test_load_model_missing_id(self, mock_config):
        """Test that load_model raises ValueError if model ID is missing."""
        mock_config.return_value.BASE_MODEL_ID = ""

        with pytest.raises(ValueError, match="BASE_MODEL_ID is not set"):
            load_model()

    @patch("src.utils.model_loader.model_info")
    def test_get_model_card_success(self, mock_model_info):
        """Test retrieving model card metadata."""
        mock_info = MagicMock()
        mock_info.id = "test-model"
        mock_info.tags = ["text-generation", "transformers"]
        mock_info.pipeline_tag = "text-generation"
        mock_info.cardData = {"license": "mit"}
        mock_model_info.return_value = mock_info

        card = get_model_card("test-model")

        assert card["id"] == "test-model"
        assert "text-generation" in card["tags"]

    @patch("src.utils.model_loader.requests.get")
    def test_validate_model_compatibility_exists(self, mock_get):
        """Test validation for an existing model."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"tags": ["transformers"]}
        mock_get.return_value = mock_response

        assert validate_model_compatibility("test-model") is True

    @patch("src.utils.model_loader.requests.get")
    def test_validate_model_compatibility_not_found(self, mock_get):
        """Test validation for a non-existing model."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        assert validate_model_model_compatibility("non-existent-model") is False