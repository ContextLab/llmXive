"""Unit tests for model selection engine"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from llmxive_automation.model_selector import ModelSelector, ModelConfig


class TestModelSelector:
    """Test cases for ModelSelector class"""
    
    def test_init(self):
        """Test ModelSelector initialization"""
        selector = ModelSelector(max_size_gb=5.0)
        assert selector.max_size_bytes == 5e9
        assert "text-generation" in selector.required_tags
        assert len(selector.fallback_models) > 0
    
    @patch('llmxive_automation.model_selector.HfApi')
    def test_get_trending_model_success(self, mock_hf_api):
        """Test successful model selection"""
        # Mock API response
        mock_model = MagicMock()
        mock_model.modelId = "test/model-instruct"
        mock_model.pipeline_tag = "text-generation"
        mock_model.likes = 100
        mock_model.downloads = 1000
        mock_model.safetensors = None
        
        mock_hf_api.return_value.list_models.return_value = [mock_model]
        
        selector = ModelSelector()
        selector.hf_api = mock_hf_api.return_value
        
        # Mock validation
        with patch.object(selector, '_validate_and_configure_model') as mock_validate:
            mock_validate.return_value = ModelConfig(
                model_id="test/model-instruct",
                model_size=2e9,
                likes=100,
                downloads=1000,
                pipeline_tag="text-generation"
            )
            
            config = selector.get_trending_model()
            
            assert config.model_id == "test/model-instruct"
            assert config.model_size == 2e9
    
    @patch('llmxive_automation.model_selector.HfApi')
    def test_get_trending_model_fallback(self, mock_hf_api):
        """Test fallback when no suitable models found"""
        mock_hf_api.return_value.list_models.return_value = []
        
        selector = ModelSelector()
        selector.hf_api = mock_hf_api.return_value
        
        config = selector.get_trending_model()
        
        assert config.model_id in selector.fallback_models
    
    def test_estimate_model_size(self):
        """Test model size estimation"""
        selector = ModelSelector()
        
        # Test with known patterns
        mock_model = MagicMock()
        mock_model.safetensors = None
        
        test_cases = [
            ("test/model-7b", 7e9),
            ("test/model-1.3b", 1.3e9),
            ("microsoft/phi-2", 2.7e9),
            ("unknown/model", 3e9),  # Default
        ]
        
        for model_id, expected_size in test_cases:
            mock_model.modelId = model_id
            size = selector._estimate_model_size(mock_model)
            assert size == expected_size
    
    def test_validate_model_size_limit(self):
        """Test model size validation"""
        selector = ModelSelector(max_size_gb=5.0)
        
        mock_model = MagicMock()
        mock_model.modelId = "test/model"
        mock_model.pipeline_tag = "text-generation"
        mock_model.likes = 100
        mock_model.downloads = 1000
        
        # Test model too large
        with patch.object(selector, '_estimate_model_size', return_value=10e9):
            config = selector._validate_and_configure_model(mock_model)
            assert config is None
        
        # Test model within limit
        with patch.object(selector, '_estimate_model_size', return_value=3e9):
            config = selector._validate_and_configure_model(mock_model)
            assert config is not None
            assert config.model_size == 3e9
    
    def test_check_quantization(self):
        """Test quantization detection"""
        selector = ModelSelector()
        
        mock_model = MagicMock()
        
        # Test GGUF detection
        mock_model.modelId = "test/model-gguf"
        quant = selector._check_quantization_available(mock_model)
        assert quant == "gguf"
        
        # Test GPTQ detection
        mock_model.modelId = "test/model-gptq"
        quant = selector._check_quantization_available(mock_model)
        assert quant == "gptq"
        
        # Test no quantization
        mock_model.modelId = "test/model"
        quant = selector._check_quantization_available(mock_model)
        assert quant is None
    
    def test_get_model_requirements(self):
        """Test getting model requirements"""
        selector = ModelSelector()
        
        # Test base requirements
        config = ModelConfig(
            model_id="test/model",
            model_size=2e9,
            likes=100,
            downloads=1000,
            pipeline_tag="text-generation"
        )
        
        reqs = selector.get_model_requirements(config)
        assert reqs["transformers"] is True
        assert reqs["torch"] is True
        
        # Test with GGUF
        config.quantization = "gguf"
        reqs = selector.get_model_requirements(config)
        assert reqs["llama-cpp-python"] is True
        
        # Test with GPTQ
        config.quantization = "gptq"
        reqs = selector.get_model_requirements(config)
        assert reqs["auto-gptq"] is True