import pytest
import torch
import torch.nn as nn
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.baseline_transformer import (
    PositionalEncoding,
    BaselineTransformer,
    create_baseline_model
)

@pytest.fixture
def dummy_input():
    """Create a dummy input tensor."""
    # Shape: (batch_size, seq_len)
    return torch.randint(0, 1000, (4, 32))

@pytest.fixture
def dummy_embedded_input():
    """Create a dummy embedded input tensor."""
    # Shape: (batch_size, seq_len, d_model)
    batch_size = 4
    seq_len = 32
    d_model = 64
    return torch.randn(batch_size, seq_len, d_model)

def test_positional_encoding_creation():
    """Test PositionalEncoding initialization and output shape."""
    d_model = 64
    max_len = 512
    pe = PositionalEncoding(d_model, max_len)
    
    assert pe.d_model == d_model
    assert pe.max_len == max_len
    assert pe.register_buffer('pe', pe.pe)
    
    # Test forward pass
    x = torch.randn(2, 10, d_model)
    output = pe(x)
    
    assert output.shape == x.shape
    # Check that positional encoding is added (not just identity)
    assert not torch.allclose(output, x)

def test_positional_encoding_zero_drop():
    """Test PositionalEncoding with dropout=0."""
    d_model = 64
    max_len = 512
    pe = PositionalEncoding(d_model, max_len, dropout=0.0)
    
    x = torch.randn(2, 10, d_model)
    output = pe(x)
    
    # With dropout=0, output should always be the same for same input
    output2 = pe(x)
    assert torch.allclose(output, output2)

def test_baseline_model_creation():
    """Test BaselineTransformer model creation."""
    config = {
        'd_model': 64,
        'nhead': 4,
        'num_layers': 2,
        'dim_feedforward': 128,
        'vocab_size': 1000
    }
    
    model = BaselineTransformer(**config)
    
    assert model.d_model == 64
    assert model.nhead == 4
    assert model.num_layers == 2
    assert model.dim_feedforward == 128
    assert model.vocab_size == 1000
    
    # Check that model has required components
    assert isinstance(model.embedding, nn.Embedding)
    assert isinstance(model.pos_encoder, PositionalEncoding)
    assert isinstance(model.transformer_encoder, nn.TransformerEncoder)
    assert isinstance(model.output_layer, nn.Linear)

def test_baseline_model_forward_pass(dummy_embedded_input):
    """Test forward pass of BaselineTransformer."""
    config = {
        'd_model': 64,
        'nhead': 4,
        'num_layers': 2,
        'dim_feedforward': 128,
        'vocab_size': 1000
    }
    
    model = BaselineTransformer(**config)
    model.eval()
    
    with torch.no_grad():
        output = model(dummy_embedded_input)
    
    batch_size, seq_len, d_model = dummy_embedded_input.shape
    assert output.shape == (batch_size, seq_len, config['vocab_size'])

def test_baseline_model_with_raw_input(dummy_input):
    """Test forward pass with raw input (token IDs)."""
    config = {
        'd_model': 64,
        'nhead': 4,
        'num_layers': 2,
        'dim_feedforward': 128,
        'vocab_size': 1000
    }
    
    model = BaselineTransformer(**config)
    model.eval()
    
    with torch.no_grad():
        output = model(dummy_input)
    
    batch_size, seq_len = dummy_input.shape
    assert output.shape == (batch_size, seq_len, config['vocab_size'])

def test_create_baseline_model_helper():
    """Test the create_baseline_model helper function."""
    config = {
        'd_model': 32,
        'nhead': 2,
        'num_layers': 1,
        'dim_feedforward': 64,
        'vocab_size': 500
    }
    
    model = create_baseline_model(**config)
    
    assert model is not None
    assert isinstance(model, BaselineTransformer)
    assert model.d_model == 32
    assert model.nhead == 2

def test_baseline_model_cpu_enforcement():
    """Test that the model can run on CPU (as required by project constraints)."""
    config = {
        'd_model': 32,
        'nhead': 2,
        'num_layers': 1,
        'dim_feedforward': 64,
        'vocab_size': 500
    }
    
    model = create_baseline_model(**config)
    model = model.cpu()
    
    dummy_input = torch.randint(0, 500, (2, 16))
    
    with torch.no_grad():
        output = model(dummy_input)
    
    assert output.device.type == 'cpu'
    assert output.shape == (2, 16, 500)

def test_baseline_model_parameter_count():
    """Test that the model has approximately the expected number of parameters."""
    config = {
        'd_model': 32,
        'nhead': 2,
        'num_layers': 1,
        'dim_feedforward': 64,
        'vocab_size': 500
    }
    
    model = create_baseline_model(**config)
    total_params = sum(p.numel() for p in model.parameters())
    
    # Rough estimate: embedding + transformer + output
    # This is a sanity check, not an exact calculation
    assert total_params > 10000  # Should be in the tens of thousands
    assert total_params < 1000000  # Should be less than 1M for this config
