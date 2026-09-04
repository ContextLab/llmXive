import pytest
import torch
import numpy as np
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from models.dreamx_lite import create_dreamx_lite_model
from utils.config import set_global_seed

@pytest.fixture
def model():
    set_global_seed(42)
    return create_dreamx_lite_model(embedding_dim=768)

def test_deterministic_output(model):
    """
    Verify that the model produces deterministic output on a fixed input.
    """
    set_global_seed(42)
    x = torch.randn(2, 768)
    extrinsics = torch.randn(2, 4, 4)
    
    # Run 1
    out1 = model(x, camera_extrinsics=extrinsics)
    
    # Reset seed
    set_global_seed(42)
    
    # Run 2
    out2 = model(x, camera_extrinsics=extrinsics)
    
    assert torch.allclose(out1, out2), "Outputs should be identical with fixed seed"

def test_deterministic_projection(model):
    """
    Verify that the projection layer is deterministic (no dropout, etc.).
    """
    set_global_seed(42)
    x = torch.randn(2, 16)
    
    out1 = model.get_camera_embedding(x)
    
    set_global_seed(42)
    out2 = model.get_camera_embedding(x)
    
    assert torch.allclose(out1, out2), "Projection should be deterministic"
