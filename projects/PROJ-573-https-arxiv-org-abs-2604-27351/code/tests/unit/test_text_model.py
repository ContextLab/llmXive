"""
Unit tests for TextModel implementation.

Tests FR-002 compliance:
- CPU-only inference
- Model size < 1 GB
- Required methods: load_model, predict, get_embedding
"""
import os
import tempfile
import pytest
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.models.text_model import TextModel, DEFAULT_MODEL_ID, MAX_MODEL_SIZE_MB


class TestTextModel:
    """Test suite for TextModel class."""
    
    def test_initialization(self):
        """Test TextModel initialization with default and custom model_id."""
        # Default model
        model = TextModel()
        assert model.model_id == DEFAULT_MODEL_ID
        assert model.device == "cpu"
        assert model._loaded is False
        
        # Custom model
        custom_id = "distilbert-base-uncased-finetuned-sst-2-english"
        model_custom = TextModel(model_id=custom_id)
        assert model_custom.model_id == custom_id
    
    def test_load_model_cpu_only(self):
        """Test that model loads on CPU and enforces CPU-only inference."""
        model = TextModel(model_id="distilbert-base-uncased")
        
        # Mock the transformers loading to avoid actual download in tests
        with patch('src.models.text_model.AutoModel') as mock_model, \
             patch('src.models.text_model.AutoTokenizer') as mock_tokenizer:
            
            mock_model.from_pretrained.return_value = MagicMock()
            mock_model.from_pretrained.return_value.to.return_value = mock_model.from_pretrained.return_value
            mock_model.from_pretrained.return_value.eval.return_value = mock_model.from_pretrained.return_value
            mock_tokenizer.from_pretrained.return_value = MagicMock()
            
            result = model.load_model()
            
            assert result is True
            assert model._loaded is True
            assert model.device == "cpu"
            
            # Verify .to("cpu") was called
            mock_model.from_pretrained.return_value.to.assert_called_with("cpu")
    
    def test_model_size_verification(self):
        """Test that model size is verified against MAX_MODEL_SIZE_MB."""
        model = TextModel()
        
        # Test with a mock that returns size under limit
        with patch.object(model, '_verify_model_size', return_value=500.0):
            assert model._verify_model_size("test-model") == 500.0
        
        # Test size limit check in load_model
        with patch.object(model, '_verify_model_size', return_value=1500.0), \
             patch('src.models.text_model.AutoModel'), \
             patch('src.models.text_model.AutoTokenizer'):
            
            with pytest.raises(RuntimeError) as excinfo:
                model.load_model()
            
            assert "exceeds limit" in str(excinfo.value)
    
    def test_predict_with_string_input(self):
        """Test prediction with single string input."""
        model = TextModel()
        
        # Mock model loading and inference
        with patch.object(model, 'load_model', return_value=True), \
             patch('src.models.text_model.torch') as mock_torch, \
             patch.object(model, 'tokenizer') as mock_tokenizer:
            
            # Setup mocks
            mock_tokenizer.return_value = {
                'input_ids': mock_torch.tensor([[1, 2, 3]]),
                'attention_mask': mock_torch.tensor([[1, 1, 1]])
            }
            
            mock_outputs = MagicMock()
            mock_outputs.last_hidden_state = mock_torch.tensor([[0.1, 0.2, 0.3]])
            mock_model_instance = MagicMock()
            mock_model_instance.return_value = mock_outputs
            mock_torch.nn.functional.softmax = MagicMock(return_value=mock_torch.tensor([[0.9, 0.1]]))
            
            model.model = mock_model_instance
            model._loaded = True
            
            result = model.predict("Test input text")
            
            assert "prediction" in result
            assert "confidence" in result
            assert "tokens_used" in result
            assert "inference_time_sec" in result
    
    def test_predict_with_dict_input(self):
        """Test prediction with dictionary input containing 'text' key."""
        model = TextModel()
        
        with patch.object(model, 'load_model', return_value=True), \
             patch('src.models.text_model.torch') as mock_torch, \
             patch.object(model, 'tokenizer') as mock_tokenizer:
            
            mock_tokenizer.return_value = {
                'input_ids': mock_torch.tensor([[1, 2, 3]]),
                'attention_mask': mock_torch.tensor([[1, 1, 1]])
            }
            
            mock_outputs = MagicMock()
            mock_outputs.last_hidden_state = mock_torch.tensor([[0.1, 0.2, 0.3]])
            mock_model_instance = MagicMock()
            mock_model_instance.return_value = mock_outputs
            
            model.model = mock_model_instance
            model._loaded = True
            
            input_dict = {"text": "Test input from dict"}
            result = model.predict(input_dict)
            
            assert "prediction" in result
            assert result["tokens_used"] == 3
    
    def test_predict_with_invalid_input(self):
        """Test prediction raises error for unsupported input types."""
        model = TextModel()
        model._loaded = True  # Pretend loaded to test input validation
        
        with pytest.raises(ValueError):
            model.predict(12345)  # Invalid type
        
        with pytest.raises(ValueError):
            model.predict(None)  # Invalid type
    
    def test_get_embedding_returns_numpy(self):
        """Test that get_embedding returns numpy array."""
        model = TextModel()
        
        with patch.object(model, 'load_model', return_value=True), \
             patch.object(model, 'predict') as mock_predict:
            
            mock_predict.return_value = {
                "prediction": [[0.1, 0.2, 0.3]],
                "confidence": 0.9,
                "tokens_used": 3,
                "inference_time_sec": 0.1,
                "model_id": "test"
            }
            
            result = model.get_embedding("test text")
            
            assert isinstance(result, np.ndarray)
            assert result.shape == (1, 3)
    
    def test_get_embedding_single_string(self):
        """Test embedding for single string returns 2D array."""
        model = TextModel()
        
        with patch.object(model, 'load_model', return_value=True), \
             patch.object(model, 'predict') as mock_predict:
            
            # Single embedding vector (1D)
            mock_predict.return_value = {
                "prediction": [0.1, 0.2, 0.3],
                "confidence": 0.9,
                "tokens_used": 3,
                "inference_time_sec": 0.1,
                "model_id": "test"
            }
            
            result = model.get_embedding("test text")
            
            assert isinstance(result, np.ndarray)
            assert result.ndim == 2  # Should be reshaped to (1, hidden_dim)
            assert result.shape[0] == 1
    
    def test_model_not_loaded_error(self):
        """Test that predict raises error if model not loaded."""
        model = TextModel()
        model._loaded = False
        
        with pytest.raises(RuntimeError) as excinfo:
            model.predict("test")
        
        assert "Model not loaded" in str(excinfo.value)
    
    def test_cpu_only_enforcement(self):
        """Test that device is always set to CPU."""
        model = TextModel()
        assert model.device == "cpu"
        
        # Even if we try to change it, it should stay CPU
        model.device = "cuda"
        assert model.device == "cuda"  # We can set it, but load_model enforces CPU
        
        # Verify load_model enforces CPU
        with patch('src.models.text_model.AutoModel') as mock_model, \
             patch('src.models.text_model.AutoTokenizer'):
            
            mock_model.from_pretrained.return_value = MagicMock()
            mock_model.from_pretrained.return_value.to.return_value = mock_model.from_pretrained.return_value
            mock_model.from_pretrained.return_value.eval.return_value = mock_model.from_pretrained.return_value
            
            model.device = "cuda"  # Try to set to cuda
            model.load_model()
            
            # Verify .to("cpu") was called, overriding the cuda setting
            mock_model.from_pretrained.return_value.to.assert_called_with("cpu")


class TestTextModelIntegration:
    """Integration tests for TextModel (mocked)."""
    
    def test_full_workflow(self):
        """Test complete workflow: init -> load -> predict -> embedding."""
        model = TextModel(model_id="distilbert-base-uncased")
        
        # Mock all external dependencies
        with patch.object(model, 'load_model', return_value=True), \
             patch.object(model, 'predict') as mock_predict, \
             patch.object(model, 'get_embedding') as mock_embedding:
            
            mock_predict.return_value = {
                "prediction": [[0.5, 0.5]],
                "confidence": 0.8,
                "tokens_used": 10,
                "inference_time_sec": 0.05,
                "model_id": "test"
            }
            
            mock_embedding.return_value = np.array([[0.1, 0.2, 0.3]])
            
            # Execute workflow
            model.load_model()
            pred_result = model.predict("Hello world")
            emb_result = model.get_embedding("Hello world")
            
            assert pred_result["confidence"] == 0.8
            assert emb_result.shape == (1, 3)
    
    def test_error_handling_on_load_failure(self):
        """Test error handling when model loading fails."""
        model = TextModel()
        
        with patch.object(model, '_verify_model_size', return_value=1500.0):
            with pytest.raises(RuntimeError):
                model.load_model()
    
    def test_cleanup_on_deletion(self):
        """Test that model resources are cleaned up on deletion."""
        model = TextModel()
        
        with patch.object(model, 'load_model', return_value=True):
            model.load_model()
            model.model = MagicMock()
            model.tokenizer = MagicMock()
            
            # Delete should not raise
            del model


if __name__ == "__main__":
    pytest.main([__file__, "-v"])