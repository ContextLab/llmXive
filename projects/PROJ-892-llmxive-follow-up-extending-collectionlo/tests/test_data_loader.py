"""
Unit tests for code/data_loader.py functions.

These tests verify the correctness of model loading, adapter handling,
and subspace rank computation.
"""
import torch
import numpy as np
from pathlib import Path
import pytest
import tempfile
import json

from data_loader import (
    compute_subspace_ranks,
    load_adapter_weights,
    save_adapter_weights
)

@pytest.fixture
def mock_adapter_weights():
    """Create mock adapter weights for testing."""
    weights = {
        'unet.down_blocks.0.attentions.0.transformer_blocks.0.attn1.to_q.lora_A.weight': 
            torch.randn(32, 64),
        'unet.down_blocks.0.attentions.0.transformer_blocks.0.attn1.to_q.lora_B.weight': 
            torch.randn(64, 32),
        'unet.down_blocks.0.attentions.0.transformer_blocks.0.attn1.to_k.lora_A.weight': 
            torch.randn(32, 64),
        'unet.down_blocks.0.attentions.0.transformer_blocks.0.attn1.to_k.lora_B.weight': 
            torch.randn(64, 32),
        'unet.down_blocks.0.attentions.0.transformer_blocks.0.attn1.to_v.lora_A.weight': 
            torch.randn(32, 64),
        'unet.down_blocks.0.attentions.0.transformer_blocks.0.attn1.to_v.lora_B.weight': 
            torch.randn(64, 32),
    }
    return weights

def test_compute_subspace_ranks(mock_adapter_weights):
    """Test subspace rank computation."""
    ranks = compute_subspace_ranks(mock_adapter_weights)
    
    assert ranks is not None
    assert isinstance(ranks, dict)
    
    # Check that ranks are computed for each effect
    for key, rank in ranks.items():
        assert isinstance(rank, int)
        assert rank > 0

def test_save_and_load_adapter_weights(mock_adapter_weights):
    """Test saving and loading adapter weights."""
    with tempfile.TemporaryDirectory() as tmpdir:
        save_path = Path(tmpdir) / "adapter_weights.pt"
        
        # Save weights
        save_adapter_weights(mock_adapter_weights, save_path)
        
        # Verify file was created
        assert save_path.exists()
        
        # Load weights
        loaded_weights = load_adapter_weights(save_path)
        
        # Verify loaded weights match
        assert loaded_weights is not None
        assert len(loaded_weights) == len(mock_adapter_weights)
        
        for key in mock_adapter_weights:
            assert torch.allclose(
                mock_adapter_weights[key], 
                loaded_weights[key],
                atol=1e-6
            )

def test_compute_subspace_ranks_different_ranks():
    """Test subspace rank computation with varying rank matrices."""
    weights = {
        'effect1.lora_A': torch.randn(10, 100),  # Rank 10
        'effect1.lora_B': torch.randn(100, 10),
        'effect2.lora_A': torch.randn(5, 50),    # Rank 5
        'effect2.lora_B': torch.randn(50, 5),
    }
    
    ranks = compute_subspace_ranks(weights)
    
    assert ranks['effect1'] == 10
    assert ranks['effect2'] == 5

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
