"""Integration test for CPU model loading."""
import pytest
import torch
import os
import sys
from src.llmxive.model_factory import load_model, SUPPORTED_MODELS
from src.llmxive.exceptions import ERR_CPU_LOAD_FAIL

class TestCPULoad:
    """Tests for CPU model loading."""
    
    @pytest.mark.parametrize("model_id", SUPPORTED_MODELS.keys())
    def test_load_cpu_model(self, model_id):
        """Test loading model on CPU without CUDA."""
        # Ensure CUDA is not used
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        model, tokenizer = load_model(model_id, device="cpu")
        
        assert model is not None
        assert tokenizer is not None
        # Verify model is on CPU
        for param in model.parameters():
            assert param.device.type == "cpu"
            break
    
    def test_load_invalid_model(self):
        """Test that invalid model raises error."""
        with pytest.raises(ValueError):
            load_model("invalid-model-id", device="cpu")
