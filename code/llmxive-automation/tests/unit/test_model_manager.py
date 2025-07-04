"""Unit tests for ModelManager with real HuggingFace models"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import torch
from transformers import PreTrainedModel, PreTrainedTokenizer

from src.model_manager import ModelManager


class TestModelManager:
    """Test suite for ModelManager"""
    
    @pytest.fixture
    def model_manager(self, tmp_path):
        """Create ModelManager instance with temp cache"""
        return ModelManager(cache_dir=str(tmp_path))
    
    def test_initialization(self, model_manager):
        """Test ModelManager initialization"""
        assert model_manager.cache_dir is not None
        assert model_manager.hf_api is not None
        assert model_manager.max_model_size_gb == 3.5
    
    @patch('src.model_manager.HfApi')
    def test_get_trending_models(self, mock_hf_api, model_manager):
        """Test getting trending models from HuggingFace"""
        # Mock model info
        mock_model = MagicMock()
        mock_model.modelId = "microsoft/phi-2"
        mock_model.downloads = 1000000
        mock_model.likes = 5000
        mock_model.tags = ["instruct", "text-generation"]
        
        mock_hf_api.return_value.list_models.return_value = [mock_model]
        mock_hf_api.return_value.model_info.return_value.safetensors = {
            "total": 2 * 1024 * 1024 * 1024  # 2GB
        }
        
        models = model_manager._get_trending_models()
        
        assert len(models) > 0
        assert models[0]["model_id"] == "microsoft/phi-2"
        assert models[0]["size_gb"] < 3.5
    
    @patch('src.model_manager.AutoModelForCausalLM')
    @patch('src.model_manager.AutoTokenizer')
    def test_load_model_success(self, mock_tokenizer, mock_model, model_manager):
        """Test successful model loading"""
        # Mock model and tokenizer
        mock_model_instance = MagicMock(spec=PreTrainedModel)
        mock_tokenizer_instance = MagicMock(spec=PreTrainedTokenizer)
        
        mock_model.from_pretrained.return_value = mock_model_instance
        mock_tokenizer.from_pretrained.return_value = mock_tokenizer_instance
        
        model_id = "microsoft/phi-2"
        model, tokenizer = model_manager._load_model(model_id)
        
        assert model is not None
        assert tokenizer is not None
        mock_model.from_pretrained.assert_called_once()
        mock_tokenizer.from_pretrained.assert_called_once()
    
    @patch('src.model_manager.AutoModelForCausalLM')
    def test_load_model_failure(self, mock_model, model_manager):
        """Test model loading failure handling"""
        mock_model.from_pretrained.side_effect = Exception("Model not found")
        
        model, tokenizer = model_manager._load_model("invalid/model")
        
        assert model is None
        assert tokenizer is None
    
    @patch.object(ModelManager, '_get_trending_models')
    @patch.object(ModelManager, '_load_model')
    def test_get_suitable_model_success(self, mock_load, mock_trending, model_manager):
        """Test getting a suitable model"""
        # Mock trending models
        mock_trending.return_value = [
            {"model_id": "microsoft/phi-2", "size_gb": 2.7},
            {"model_id": "TinyLlama/TinyLlama-1.1B", "size_gb": 1.1}
        ]
        
        # Mock successful load
        mock_model = MagicMock()
        mock_tokenizer = MagicMock()
        mock_load.return_value = (mock_model, mock_tokenizer)
        
        model, tokenizer = model_manager.get_suitable_model()
        
        assert model is not None
        assert tokenizer is not None
        mock_load.assert_called_once_with("microsoft/phi-2")
    
    @patch.object(ModelManager, '_get_trending_models')
    @patch.object(ModelManager, '_load_model')
    def test_get_suitable_model_fallback(self, mock_load, mock_trending, model_manager):
        """Test fallback to default model"""
        # Mock no trending models
        mock_trending.return_value = []
        
        # Mock successful load of fallback
        mock_model = MagicMock()
        mock_tokenizer = MagicMock()
        mock_load.return_value = (mock_model, mock_tokenizer)
        
        model, tokenizer = model_manager.get_suitable_model()
        
        assert model is not None
        assert tokenizer is not None
        # Should try to load default model
        assert mock_load.call_count > 0
    
    def test_check_model_size(self, model_manager):
        """Test model size checking"""
        # Test various model IDs and expected behaviors
        test_cases = [
            ("microsoft/phi-2", True),  # Known small model
            ("meta-llama/Llama-2-70b", False),  # Known large model
            ("TinyLlama/TinyLlama-1.1B", True),  # Known tiny model
        ]
        
        with patch.object(model_manager.hf_api, 'model_info') as mock_info:
            for model_id, expected_fits in test_cases:
                # Mock different sizes
                if "70b" in model_id:
                    size = 140 * 1024 * 1024 * 1024  # 140GB
                elif "TinyLlama" in model_id:
                    size = 1.1 * 1024 * 1024 * 1024  # 1.1GB
                else:
                    size = 2.7 * 1024 * 1024 * 1024  # 2.7GB
                
                mock_info.return_value.safetensors = {"total": size}
                
                result = model_manager._check_model_size(model_id)
                assert result == expected_fits
    
    @pytest.mark.integration
    @pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
    def test_model_memory_usage(self, model_manager):
        """Test actual memory usage with quantization"""
        # This test would load a real small model if run
        # Skip in CI/CD, run locally with GPU
        pass
    
    def test_model_loading_with_quantization(self, model_manager):
        """Test 4-bit quantization configuration"""
        with patch('src.model_manager.AutoModelForCausalLM.from_pretrained') as mock_load:
            mock_model = MagicMock()
            mock_load.return_value = mock_model
            
            model, _ = model_manager._load_model("test/model", use_4bit=True)
            
            # Check quantization config was passed
            args, kwargs = mock_load.call_args
            assert 'quantization_config' in kwargs
            assert kwargs['device_map'] == "auto"
    
    @patch('src.model_manager.HfApi')
    def test_filter_suitable_models(self, mock_api, model_manager):
        """Test filtering models by various criteria"""
        # Create mock models with different properties
        models = []
        for i in range(5):
            model = MagicMock()
            model.modelId = f"model-{i}"
            model.downloads = 1000 * (5 - i)
            model.likes = 100 * (5 - i)
            model.tags = ["text-generation"]
            if i < 3:
                model.tags.append("instruct")
            models.append(model)
        
        mock_api.return_value.list_models.return_value = models
        mock_api.return_value.model_info.return_value.safetensors = {
            "total": 2 * 1024 * 1024 * 1024
        }
        
        filtered = model_manager._get_trending_models()
        
        # Should prefer instruct models
        assert all("instruct" in m.get("tags", []) for m in filtered[:3])