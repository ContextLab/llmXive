"""
Unit tests for MoebiusTiny model.

Tests verify:
- Parameter count is within 15M limit
- Forward pass produces correct output shape
- Rank modulation integration works
- CPU compatibility
"""

import torch
import pytest
from pathlib import Path

# Ensure project root is in path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from models.moebius_tiny import MoebiusTiny, create_moebius_tiny
from models.data_models import InferenceResult, GatingState


class TestMoebiusTinyArchitecture:
    """Tests for model architecture and parameter constraints."""
    
    def test_parameter_count_within_limit(self):
        """Verify total parameters do not exceed 15M."""
        model = create_moebius_tiny()
        param_count = model.get_parameter_count()
        assert param_count <= 15_000_000, f"Parameter count {param_count:,} exceeds 15M limit"
        print(f"✓ Parameter count: {param_count:,} (within 15M limit)")
    
    def test_initialization(self):
        """Verify model initializes without errors."""
        model = create_moebius_tiny()
        assert model is not None
        assert isinstance(model, MoebiusTiny)
        
    def test_forward_pass_basic(self):
        """Test basic forward pass with dummy input."""
        model = create_moebius_tiny()
        model.eval()
        
        # Input: (batch, channels=4, H, W)
        input_tensor = torch.randn(1, 4, 64, 64)
        
        with torch.no_grad():
            result = model(input_tensor)
        
        assert isinstance(result, InferenceResult)
        assert result.image.shape == (1, 3, 64, 64), f"Expected (1, 3, 64, 64), got {result.image.shape}"
        
    def test_forward_pass_batch(self):
        """Test forward pass with batch input."""
        model = create_moebius_tiny()
        model.eval()
        
        input_tensor = torch.randn(4, 4, 128, 128)
        
        with torch.no_grad():
            result = model(input_tensor)
        
        assert result.image.shape == (4, 3, 128, 128)
        
    def test_output_range_tanh(self):
        """Verify output is in [-1, 1] range due to Tanh activation."""
        model = create_moebius_tiny()
        model.eval()
        
        input_tensor = torch.randn(1, 4, 64, 64)
        
        with torch.no_grad():
            result = model(input_tensor)
        
        assert result.image.min() >= -1.0
        assert result.image.max() <= 1.0
        
    def test_cpu_compatibility(self):
        """Verify model runs on CPU (no CUDA required)."""
        model = create_moebius_tiny()
        model.cpu()
        
        input_tensor = torch.randn(1, 4, 32, 32)
        
        with torch.no_grad():
            result = model(input_tensor)
        
        assert result.image.device.type == "cpu"

class TestRankModulation:
    """Tests for rank modulation functionality."""
    
    def test_set_rank_modulation(self):
        """Test setting rank modulation externally."""
        model = create_moebius_tiny()
        model.set_rank_modulation(3.0)
        
        assert model.gating_state is not None
        assert model.gating_state.rank == 3.0
        
    def test_forward_with_modulation(self):
        """Test forward pass with explicit rank modulation."""
        model = create_moebius_tiny()
        model.eval()
        
        input_tensor = torch.randn(1, 4, 64, 64)
        
        with torch.no_grad():
            result = model(input_tensor, rank_modulation=2.5)
        
        assert result.gating_state is not None
        assert result.gating_state.rank == 2.5
        assert result.metadata.get("modulation_applied") is True
        
    def test_metadata_inclusion(self):
        """Verify metadata is included in result."""
        model = create_moebius_tiny()
        model.eval()
        
        input_tensor = torch.randn(1, 4, 64, 64)
        
        with torch.no_grad():
            result = model(input_tensor)
        
        assert "input_shape" in result.metadata
        assert result.metadata["input_shape"] == input_tensor.shape

class TestEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_small_input(self):
        """Test with very small input (32x32)."""
        model = create_moebius_tiny()
        model.eval()
        
        input_tensor = torch.randn(1, 4, 32, 32)
        
        with torch.no_grad():
            result = model(input_tensor)
        
        assert result.image.shape == (1, 3, 32, 32)
        
    def test_large_input(self):
        """Test with larger input (256x256)."""
        model = create_moebius_tiny()
        model.eval()
        
        input_tensor = torch.randn(1, 4, 256, 256)
        
        with torch.no_grad():
            result = model(input_tensor)
        
        assert result.image.shape == (1, 3, 256, 256)
        
    def test_single_channel_mask_input(self):
        """Test that input must have 4 channels (RGB + Mask)."""
        model = create_moebius_tiny()
        model.eval()
        
        # Wrong number of channels
        input_tensor = torch.randn(1, 3, 64, 64)
        
        with pytest.raises(RuntimeError):
            with torch.no_grad():
                model(input_tensor)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])