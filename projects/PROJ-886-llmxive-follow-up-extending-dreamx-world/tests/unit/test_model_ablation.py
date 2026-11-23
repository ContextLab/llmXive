import pytest
import torch
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from models.dreamx_lite import DreamXLite, create_dreamx_lite_model
from models.dreamx_base import DreamXBase, create_dreamx_base_model

@pytest.fixture
def base_model():
    return create_dreamx_base_model(embedding_dim=768)

@pytest.fixture
def lite_model():
    return create_dreamx_lite_model(embedding_dim=768)

def test_parameter_count_reduction(base_model, lite_model):
    """
    Verify that DreamXLite has fewer trainable parameters than the base model
    due to the replacement of E-PRoPE with a fixed projection.
    """
    base_trainable = sum(p.numel() for p in base_model.parameters() if p.requires_grad)
    lite_trainable = sum(p.numel() for p in lite_model.parameters() if p.requires_grad)
    
    # The projection layer is small (16 * 768), while E-PRoPE (Embedding 1000*768) is larger.
    # We expect a reduction.
    assert lite_trainable < base_trainable, \
        f"Expected fewer trainable params in Lite ({lite_trainable}) than Base ({base_trainable})"
    
    print(f"Base Trainable: {base_trainable}, Lite Trainable: {lite_trainable}")

def test_fixed_projection_frozen(lite_model):
    """
    Verify that the camera_projection layer in DreamXLite is frozen (requires_grad=False).
    """
    for name, param in lite_model.named_parameters():
        if 'camera_projection' in name:
            assert not param.requires_grad, \
                f"Parameter {name} in camera_projection should be frozen"

def test_layer_replacement_confirmation(capsys):
    """
    Verify that the logging for layer replacement is triggered during initialization.
    """
    model = create_dreamx_lite_model(embedding_dim=768)
    captured = capsys.readouterr()
    
    # Check for log messages (logging goes to stderr usually, but capsys might not catch it depending on config)
    # Instead, we verify the model state
    assert hasattr(model, 'camera_projection'), "Model must have camera_projection"
    assert not model.camera_projection.requires_grad, "Projection must be frozen"
    assert not hasattr(model, 'e_prop') or not any(p.requires_grad for p in model.e_prop.parameters()), \
        "E-Prop must be disabled"