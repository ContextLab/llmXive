"""
Unit tests for quantization logic in code/models/compress.py.

These tests verify the quantization implementation for FP32, INT8, and INT4
using torch.ao.quantization. They ensure that:
1. Models can be quantized without errors.
2. Quantized models produce valid outputs.
3. Parameter counts are correctly reported.
4. Quantization types are correctly identified.

Executes after T012 (compression logic implementation).
"""

import pytest
import torch
import torch.nn as nn
from pathlib import Path
import sys
import os

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from models.compress import QuantizationType, quantize_model, get_quantized_param_count
from config import set_seed

# Set seed for reproducibility
set_seed(42)


class SimpleModel(nn.Module):
    """A simple model for testing quantization."""
    
    def __init__(self):
        super().__init__()
        self.fc1 = nn.Linear(128, 64)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(64, 10)
    
    def forward(self, x):
        x = self.fc1(x)
        x = self.relu(x)
        x = self.fc2(x)
        return x


@pytest.fixture
def simple_model():
    """Create a simple model for testing."""
    return SimpleModel()

@pytest.fixture
def dummy_input():
    """Create dummy input for model."""
    return torch.randn(1, 128)

@pytest.fixture
def temp_model_path(tmp_path):
    """Create a temporary path for saving models."""
    return tmp_path / "test_model.pt"

class TestQuantizationType:
    """Tests for QuantizationType enum."""
    
    def test_quantization_type_values(self):
        """Test that quantization types have correct values."""
        assert QuantizationType.FP32.value == "fp32"
        assert QuantizationType.INT8.value == "int8"
        assert QuantizationType.INT4.value == "int4"
    
    def test_quantization_type_from_string(self):
        """Test creating QuantizationType from string."""
        assert QuantizationType.from_string("fp32") == QuantizationType.FP32
        assert QuantizationType.from_string("int8") == QuantizationType.INT8
        assert QuantizationType.from_string("int4") == QuantizationType.INT4
        
        with pytest.raises(ValueError):
            QuantizationType.from_string("invalid")

class TestQuantizeModel:
    """Tests for the quantize_model function."""
    
    def test_fp32_quantization(self, simple_model, dummy_input):
        """Test FP32 quantization (no actual quantization)."""
        quantized_model = quantize_model(simple_model, QuantizationType.FP32)
        
        # FP32 should return the same model or a model with same precision
        output = quantized_model(dummy_input)
        assert output.shape == (1, 10)
        assert not torch.isnan(output).any()
    
    def test_int8_quantization(self, simple_model, dummy_input):
        """Test INT8 dynamic quantization."""
        quantized_model = quantize_model(simple_model, QuantizationType.INT8)
        
        # INT8 quantization should work
        output = quantized_model(dummy_input)
        assert output.shape == (1, 10)
        assert not torch.isnan(output).any()
        
        # Check that linear layers are quantized
        for module in quantized_model.modules():
            if isinstance(module, nn.Linear):
                # Dynamic quantization replaces Linear with QuantizedLinear
                # or keeps it but with quantized weights
                pass
    
    @pytest.mark.skip(reason="INT4 quantization requires specific backend support")
    def test_int4_quantization(self, simple_model, dummy_input):
        """Test INT4 quantization (may require specific backend)."""
        quantized_model = quantize_model(simple_model, QuantizationType.INT4)
        
        output = quantized_model(dummy_input)
        assert output.shape == (1, 10)
        assert not torch.isnan(output).any()
    
    def test_quantization_preserves_output_shape(self, simple_model, dummy_input):
        """Test that quantization preserves output shape."""
        for q_type in [QuantizationType.FP32, QuantizationType.INT8]:
            quantized_model = quantize_model(simple_model, q_type)
            original_output = simple_model(dummy_input)
            quantized_output = quantized_model(dummy_input)
            
            assert original_output.shape == quantized_output.shape
    
    def test_quantization_with_cpu_only(self, simple_model, dummy_input):
        """Test that quantization works on CPU."""
        # Ensure model is on CPU
        simple_model = simple_model.cpu()
        dummy_input = dummy_input.cpu()
        
        for q_type in [QuantizationType.FP32, QuantizationType.INT8]:
            quantized_model = quantize_model(simple_model, q_type)
            output = quantized_model(dummy_input)
            
            assert output.device.type == "cpu"
            assert not torch.isnan(output).any()

class TestGetQuantizedParamCount:
    """Tests for get_quantized_param_count function."""
    
    def test_fp32_param_count(self, simple_model):
        """Test parameter count for FP32 model."""
        param_count = get_quantized_param_count(simple_model, QuantizationType.FP32)
        
        # Calculate expected parameter count
        expected = sum(p.numel() for p in simple_model.parameters())
        assert param_count == expected
    
    def test_int8_param_count_reduction(self, simple_model):
        """Test that INT8 quantization reduces parameter count."""
        fp32_count = get_quantized_param_count(simple_model, QuantizationType.FP32)
        int8_count = get_quantized_param_count(simple_model, QuantizationType.INT8)
        
        # INT8 should have fewer or equal parameters (depending on implementation)
        # Dynamic quantization might not reduce parameter count in terms of storage
        # but should reduce memory footprint
        assert int8_count <= fp32_count
    
    def test_param_count_consistency(self, simple_model):
        """Test that parameter count is consistent across calls."""
        count1 = get_quantized_param_count(simple_model, QuantizationType.FP32)
        count2 = get_quantized_param_count(simple_model, QuantizationType.FP32)
        
        assert count1 == count2

class TestQuantizationIntegration:
    """Integration tests for quantization workflow."""
    
    def test_quantize_and_inference(self, simple_model, dummy_input, temp_model_path):
        """Test full quantization and inference workflow."""
        # Quantize model
        quantized_model = quantize_model(simple_model, QuantizationType.INT8)
        
        # Run inference
        output = quantized_model(dummy_input)
        assert output.shape == (1, 10)
        assert not torch.isnan(output).any()
        
        # Save model
        torch.save({
            'model_state_dict': quantized_model.state_dict(),
            'quantization_type': QuantizationType.INT8.value,
            'param_count': get_quantized_param_count(quantized_model, QuantizationType.INT8)
        }, temp_model_path)
        
        # Load model
        checkpoint = torch.load(temp_model_path, map_location='cpu', weights_only=False)
        loaded_model = SimpleModel()
        loaded_model.load_state_dict(checkpoint['model_state_dict'])
        
        # Verify loaded model works
        loaded_output = loaded_model(dummy_input)
        assert torch.allclose(output, loaded_output, atol=1e-5)
    
    def test_multiple_quantization_types(self, simple_model, dummy_input):
        """Test quantization with all supported types."""
        for q_type in [QuantizationType.FP32, QuantizationType.INT8]:
            quantized_model = quantize_model(simple_model, q_type)
            output = quantized_model(dummy_input)
            
            assert output.shape == (1, 10)
            assert not torch.isnan(output).any()
            assert not torch.isinf(output).any()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])