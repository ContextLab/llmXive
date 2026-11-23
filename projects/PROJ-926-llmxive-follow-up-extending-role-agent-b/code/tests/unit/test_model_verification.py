"""
Unit tests for T046: Real Data Source Verification.

These tests verify that the trajectory generator correctly handles
model loading and fails loudly if the model is inaccessible.
"""
import json
import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

# Import the function to test
from src.sim.trajectory_generator import verify_model_accessibility, load_model_and_tokenizer

class TestModelVerification:
    
    def test_verify_success_writes_log(self, tmp_path):
        """Test that successful verification writes a log with status SUCCESS."""
        # Mock the transformers loading to simulate success
        mock_model = MagicMock()
        mock_model.config.model_type = "llama"
        mock_tokenizer = MagicMock()
        
        with patch('src.sim.trajectory_generator.AutoModelForCausalLM.from_pretrained', return_value=mock_model), \
             patch('src.sim.trajectory_generator.AutoTokenizer.from_pretrained', return_value=mock_tokenizer):
            
            log_path = os.path.join(tmp_path, "log.json")
            result = verify_model_accessibility("meta-llama/Llama-3-8B", output_path=log_path)
            
            assert result is True
            assert os.path.exists(log_path)
            
            with open(log_path, 'r') as f:
                log_data = json.load(f)
            
            assert log_data["status"] == "SUCCESS"
            assert log_data["model_id"] == "meta-llama/Llama-3-8B"
            assert log_data["error_message"] is None
            assert "timestamp" in log_data

    def test_verify_failure_raises_and_writes_log(self, tmp_path):
        """Test that failure to load model raises RuntimeError and writes FAILED log."""
        from transformers import RepositoryNotFoundError
        
        mock_error = RepositoryNotFoundError("Model not found")
        
        with patch('src.sim.trajectory_generator.AutoModelForCausalLM.from_pretrained', side_effect=mock_error):
            
            log_path = os.path.join(tmp_path, "log.json")
            
            # Should raise RuntimeError
            with pytest.raises(RuntimeError) as exc_info:
                verify_model_accessibility("meta-llama/Llama-3-8B", output_path=log_path)
            
            assert "Model verification failed" in str(exc_info.value)
            
            # Log should still be written
            assert os.path.exists(log_path)
            
            with open(log_path, 'r') as f:
                log_data = json.load(f)
            
            assert log_data["status"] == "FAILED"
            assert log_data["error_message"] is not None
            assert "Model not found" in log_data["error_message"]

    def test_load_model_forces_cpu_and_float32(self):
        """Test that load_model_and_tokenizer enforces CPU and float32."""
        mock_model = MagicMock()
        mock_model.config.model_type = "llama"
        mock_tokenizer = MagicMock()
        
        with patch('src.sim.trajectory_generator.AutoModelForCausalLM.from_pretrained', return_value=mock_model), \
             patch('src.sim.trajectory_generator.AutoTokenizer.from_pretrained', return_value=mock_tokenizer), \
             patch('torch.device') as mock_device:
            
            # Simulate CPU device
            mock_device.return_value = 'cpu'
            
            model, tokenizer = load_model_and_tokenizer("meta-llama/Llama-3-8B")
            
            # Verify from_pretrained was called with correct args
            call_args = mock_model.from_pretrained.call_args
            assert call_args[1]['torch_dtype'] == 'torch.float32' # Note: mocked, but logic check
            assert call_args[1]['device_map'] == 'cpu'
            assert call_args[1]['use_cache'] == False
