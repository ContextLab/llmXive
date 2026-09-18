"""Unit tests for model factory."""
import pytest
from unittest.mock import patch, MagicMock
import sys
import os
from src.llmxive.model_factory import load_model, SUPPORTED_MODELS, ERR_CPU_LOAD_FAIL
from src.llmxive.exceptions import ERR_CPU_LOAD_FAIL as ERR_CLASS

class TestModelFactory:
    """Tests for model loading."""
    
    @patch('src.llmxive.model_factory.AutoModelForCausalLM.from_pretrained')
    @patch('src.llmxive.model_factory.AutoTokenizer.from_pretrained')
    def test_load_phi2(self, mock_tokenizer, mock_model):
        """Test loading Phi-2 model."""
        mock_model.return_value = MagicMock(to=MagicMock(return_value=MagicMock()))
        mock_tokenizer.return_value = MagicMock()
        
        model, tokenizer = load_model("phi-2", device="cpu")
        
        assert model is not None
        assert tokenizer is not None
    
    @patch('src.llmxive.model_factory.AutoModelForCausalLM.from_pretrained')
    @patch('src.llmxive.model_factory.AutoTokenizer.from_pretrained')
    def test_load_qwen(self, mock_tokenizer, mock_model):
        """Test loading Qwen model."""
        mock_model.return_value = MagicMock(to=MagicMock(return_value=MagicMock()))
        mock_tokenizer.return_value = MagicMock()
        
        model, tokenizer = load_model("qwen1.5-1.8b", device="cpu")
        
        assert model is not None
        assert tokenizer is not None
    
    def test_invalid_model_id(self):
        """Test that invalid model ID raises error."""
        with pytest.raises(ValueError):
            load_model("invalid-model", device="cpu")
    
    @patch('src.llmxive.model_factory.AutoModelForCausalLM.from_pretrained')
    @patch('src.llmxive.model_factory.AutoTokenizer.from_pretrained')
    def test_load_fail_raises_error(self, mock_tokenizer, mock_model):
        """Test that load failure raises ERR_CPU_LOAD_FAIL."""
        mock_model.side_effect = Exception("OOM")
        
        with pytest.raises(ERR_CPU_LOAD_FAIL):
            load_model("phi-2", device="cpu")
