import pytest
import torch
import torch.nn as nn
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.spiking_transformer import (
    SpikingFeedForward,
    SpikingTransformerEncoderLayer,
    SpikingTransformer,
    create_spiking_model,
    verify_surrogate_gradients
)

@pytest.fixture
def dummy_input():
    """Create a dummy input tensor."""
    # Shape: (batch_size, seq_len, d_model)
    return torch.randn(4, 32, 64)

def test_spiking_feed_forward_creation():
    """Test SpikingFeedForward initialization."""
    d_model = 64
    dim_feedforward = 128
    num_steps = 5
    
    sff = SpikingFeedForward(d_model, dim_feedforward, num_steps)
    
    assert sff.d_model == d_model
    assert sff.dim_feedforward == dim_feedforward
    assert sff.num_steps == num_steps
    assert isinstance(sff.fc1, nn.Linear)
    assert isinstance(sff.fc2, nn.Linear)
    # Check that LIF neurons are present
    assert hasattr(sff, 'lif1')
    assert hasattr(sff, 'lif2')

def test_spiking_feed_forward_forward_pass(dummy_input):
    """Test forward pass of SpikingFeedForward."""
    d_model = 64
    dim_feedforward = 128
    num_steps = 5
    
    sff = SpikingFeedForward(d_model, dim_feedforward, num_steps)
    sff.eval()
    
    with torch.no_grad():
        output = sff(dummy_input)
    
    assert output.shape == dummy_input.shape
    # Output should contain spike values (0 or 1, or continuous approximation)
    assert output.min() >= 0.0
    assert output.max() <= 1.0

def test_spiking_feed_forward_with_different_steps():
    """Test SpikingFeedForward with different time steps."""
    d_model = 32
    dim_feedforward = 64
    
    for num_steps in [1, 3, 5, 10]:
        sff = SpikingFeedForward(d_model, dim_feedforward, num_steps)
        dummy = torch.randn(2, 16, d_model)
        
        output = sff(dummy)
        assert output.shape == dummy.shape

def test_spiking_transformer_encoder_layer_creation():
    """Test SpikingTransformerEncoderLayer initialization."""
    d_model = 64
    nhead = 4
    dim_feedforward = 128
    num_steps = 5
    
    layer = SpikingTransformerEncoderLayer(d_model, nhead, dim_feedforward, num_steps)
    
    assert layer.d_model == d_model
    assert layer.nhead == nhead
    assert layer.dim_feedforward == dim_feedforward
    assert layer.num_steps == num_steps
    assert isinstance(layer.self_attn, nn.MultiheadAttention)
    assert isinstance(layer.ff, SpikingFeedForward)

def test_spiking_transformer_encoder_layer_forward(dummy_input):
    """Test forward pass of SpikingTransformerEncoderLayer."""
    d_model = 64
    nhead = 4
    dim_feedforward = 128
    num_steps = 5
    
    layer = SpikingTransformerEncoderLayer(d_model, nhead, dim_feedforward, num_steps)
    layer.eval()
    
    with torch.no_grad():
        output = layer(dummy_input)
    
    assert output.shape == dummy_input.shape

def test_spiking_transformer_creation():
    """Test SpikingTransformer model creation."""
    config = {
        'd_model': 64,
        'nhead': 4,
        'num_layers': 2,
        'dim_feedforward': 128,
        'vocab_size': 1000,
        'num_steps': 5
    }
    
    model = SpikingTransformer(**config)
    
    assert model.d_model == 64
    assert model.nhead == 4
    assert model.num_layers == 2
    assert model.dim_feedforward == 128
    assert model.vocab_size == 1000
    assert model.num_steps == 5
    
    # Check that model has required components
    assert isinstance(model.embedding, nn.Embedding)
    assert len(model.encoder_layers) == config['num_layers']
    assert isinstance(model.output_layer, nn.Linear)

def test_spiking_transformer_forward_pass(dummy_input):
    """Test forward pass of SpikingTransformer."""
    config = {
        'd_model': 64,
        'nhead': 4,
        'num_layers': 2,
        'dim_feedforward': 128,
        'vocab_size': 1000,
        'num_steps': 5
    }
    
    model = SpikingTransformer(**config)
    model.eval()
    
    with torch.no_grad():
        output = model(dummy_input)
    
    batch_size, seq_len, d_model = dummy_input.shape
    assert output.shape == (batch_size, seq_len, config['vocab_size'])

def test_create_spiking_model_helper():
    """Test the create_spiking_model helper function."""
    config = {
        'd_model': 32,
        'nhead': 2,
        'num_layers': 1,
        'dim_feedforward': 64,
        'vocab_size': 500,
        'num_steps': 3
    }
    
    model = create_spiking_model(**config)
    
    assert model is not None
    assert isinstance(model, SpikingTransformer)
    assert model.d_model == 32
    assert model.num_steps == 3

def test_verify_surrogate_gradients():
    """Test the surrogate gradient verification function."""
    config = {
        'd_model': 32,
        'nhead': 2,
        'num_layers': 1,
        'dim_feedforward': 64,
        'vocab_size': 500,
        'num_steps': 3
    }
    
    model = create_spiking_model(**config)
    model.train()
    
    # Create dummy input and target
    dummy_input = torch.randn(2, 16, config['d_model'])
    target = torch.randn(2, 16, config['vocab_size'])
    
    # Forward pass
    output = model(dummy_input)
    
    # Compute loss
    loss = nn.MSELoss()(output, target)
    
    # Backward pass
    loss.backward()
    
    # Verify gradients
    is_valid, message = verify_surrogate_gradients(model)
    
    assert is_valid
    assert "No NaN gradients" in message or "All gradients are valid" in message

def test_spiking_model_cpu_enforcement():
    """Test that the spiking model can run on CPU."""
    config = {
        'd_model': 32,
        'nhead': 2,
        'num_layers': 1,
        'dim_feedforward': 64,
        'vocab_size': 500,
        'num_steps': 3
    }
    
    model = create_spiking_model(**config)
    model = model.cpu()
    
    dummy_input = torch.randn(2, 16, 32)
    
    with torch.no_grad():
        output = model(dummy_input)
    
    assert output.device.type == 'cpu'
    assert output.shape == (2, 16, 500)

def test_spiking_model_with_zero_spikes():
    """Test behavior when neurons produce zero spikes."""
    config = {
        'd_model': 32,
        'nhead': 2,
        'num_layers': 1,
        'dim_feedforward': 64,
        'vocab_size': 500,
        'num_steps': 5
    }
    
    model = create_spiking_model(**config)
    model.eval()
    
    # Create input that might result in zero spikes
    # (very low values)
    dummy_input = torch.randn(2, 16, 32) * 0.001
    
    with torch.no_grad():
        output = model(dummy_input)
    
    # Output should still be valid (even if all zeros)
    assert output.shape == (2, 16, 500)
    assert not torch.isnan(output).any()
    assert not torch.isinf(output).any()