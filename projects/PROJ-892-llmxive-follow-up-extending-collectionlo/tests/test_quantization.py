"""
Unit tests for code/data_loader.py quantization functions.

These tests verify the correctness of LoRA adapter quantization
from FP16 to INT8 and INT4.
"""
import torch
import numpy as np
from pathlib import Path
import pytest
import tempfile
import os

# Import the functions to test
from data_loader import (
    apply_quantization,
    quantize_adapter_fp16_to_int8,
    quantize_adapter_fp16_to_int4
)

@pytest.fixture
def mock_fp16_adapter():
    """Create a mock FP16 adapter state dict."""
    # Create a simple mock state dict with FP16 tensors
    state_dict = {
        'unet.down_blocks.0.attentions.0.transformer_blocks.0.attn1.to_q.lora_A.weight': 
            torch.randn(32, 64, dtype=torch.float16),
        'unet.down_blocks.0.attentions.0.transformer_blocks.0.attn1.to_q.lora_B.weight': 
            torch.randn(64, 32, dtype=torch.float16),
        'unet.down_blocks.0.attentions.0.transformer_blocks.0.attn1.to_k.lora_A.weight': 
            torch.randn(32, 64, dtype=torch.float16),
        'unet.down_blocks.0.attentions.0.transformer_blocks.0.attn1.to_k.lora_B.weight': 
            torch.randn(64, 32, dtype=torch.float16),
    }
    return state_dict

def test_quantize_fp16_to_int8(mock_fp16_adapter):
    """Test FP16 to INT8 quantization."""
    quantized_state_dict = quantize_adapter_fp16_to_int8(mock_fp16_adapter)
    
    assert quantized_state_dict is not None
    assert len(quantized_state_dict) == len(mock_fp16_adapter)
    
    # Check that quantized tensors are in INT8 range
    for key, tensor in quantized_state_dict.items():
        assert tensor.dtype == torch.int8
        assert torch.all(tensor >= -128)
        assert torch.all(tensor <= 127)

def test_quantize_fp16_to_int4(mock_fp16_adapter):
    """Test FP16 to INT4 quantization."""
    quantized_state_dict = quantize_adapter_fp16_to_int4(mock_fp16_adapter)
    
    assert quantized_state_dict is not None
    assert len(quantized_state_dict) == len(mock_fp16_adapter)
    
    # Check that quantized tensors are in INT4 range (stored as int8)
    for key, tensor in quantized_state_dict.items():
        # INT4 values stored in int8 should be in range [-8, 7]
        assert torch.all(tensor >= -8)
        assert torch.all(tensor <= 7)

def test_apply_quantization_invalid_method(mock_fp16_adapter):
    """Test that invalid quantization method raises an error."""
    with pytest.raises(ValueError):
        apply_quantization(mock_fp16_adapter, method="invalid_method")

def test_apply_quantization_int8(mock_fp16_adapter):
    """Test apply_quantization with INT8 method."""
    quantized_state_dict = apply_quantization(mock_fp16_adapter, method="int8")
    
    assert quantized_state_dict is not None
    for key, tensor in quantized_state_dict.items():
        assert tensor.dtype == torch.int8

def test_apply_quantization_int4(mock_fp16_adapter):
    """Test apply_quantization with INT4 method."""
    quantized_state_dict = apply_quantization(mock_fp16_adapter, method="int4")
    
    assert quantized_state_dict is not None
    for key, tensor in quantized_state_dict.items():
        # INT4 values stored in int8
        assert torch.all(tensor >= -8)
        assert torch.all(tensor <= 7)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
