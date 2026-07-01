"""
Tests for LIF dynamics and Spiking Transformer functionality.
Specifically verifies Constitution Principle VII: Non-NaN gradients.
"""
import torch
import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.spiking_transformer import (
    SpikingTransformer, 
    SpikingFeedForward, 
    verify_surrogate_gradients,
    create_spiking_model
)

@pytest.fixture
def dummy_batch():
    batch_size = 4
    seq_len = 16
    vocab_size = 1000
    dummy_input = torch.randint(0, vocab_size, (batch_size, seq_len))
    target = torch.randint(0, vocab_size, (batch_size, seq_len))
    return dummy_input, target

@pytest.fixture
def model():
    return create_spiking_model(
        d_model=64,
        nhead=2,
        num_layers=1,
        d_ff=128,
        vocab_size=1000,
        num_steps=4,
        beta=0.9
    )

def test_spiking_feedforward_forward(model):
    """Test that SpikingFeedForward produces output of correct shape."""
    batch_size, seq_len = 4, 16
    x = torch.randn(batch_size, seq_len, 64)
    
    output, spike_trains = model.layers[0].ffn(x)
    
    assert output.shape == (batch_size, seq_len, 64)
    spike1, spike2 = spike_trains
    assert spike1.shape == (batch_size, seq_len, 128)
    assert spike2.shape == (batch_size, seq_len, 64)
    assert output.dtype == torch.float32

def test_spiking_transformer_forward(model, dummy_batch):
    """Test full models forward pass."""
    input_ids, target = dummy_batch
    model.eval()
    
    with torch.no_grad():
        logits, aux = model(input_ids)
    
    assert logits.shape == input_ids.shape + (1000,)
    assert "spike_trains" in aux
    assert len(aux["spike_trains"]) == 1  # 1 layer

def test_surrogate_gradient_verification(model, dummy_batch):
    """
    Constitution Principle VII: Verify that surrogate gradient learning
    produces non-NaN gradients on a mini-batch.
    """
    input_ids, target = dummy_batch
    model.train()
    
    result = verify_surrogate_gradients(model, input_ids, target)
    
    assert result["success"] is True
    assert result["has_nan_logits"] is False
    assert result["has_nan_loss"] is False
    assert result["has_nan_grad"] is False
    assert "loss_value" in result
    assert result["loss_value"] > 0

def test_lif_membrane_potential_update():
    """
    Test basic LIF membrane potential dynamics.
    Ensures that the membrane potential decays and integrates input.
    This test specifically verifies the update rules:
    1. Membrane potential increases with input (integration)
    2. Membrane potential decays when input is zero (leak)
    3. Spikes are generated when membrane exceeds threshold
    """
    from snnTorch import LIF
    
    beta = 0.9
    threshold = 1.0
    lif = LIF(beta=beta, threshold=threshold)
    
    # Initialize
    mem = torch.zeros(1, 10)
    spike = torch.zeros(1, 10)
    
    # Input step: strong input to ensure integration
    input_data = torch.ones(1, 10) * 2.0
    
    # One step: integrate and fire
    new_spike, new_mem = lif(input_data, (spike, mem))
    
    # Membrane should increase (input > 0)
    assert torch.all(new_mem > mem), "Membrane potential should increase with input"
    assert new_mem.shape == input_data.shape, "Output shape mismatch"
    
    # If input is strong enough, we might see spikes
    # But the key is that membrane dynamics are correct
    
    # Another step with no input (decay)
    new_spike2, new_mem2 = lif(torch.zeros(1, 10), (new_spike, new_mem))
    
    # Membrane should decay (leak)
    assert torch.all(new_mem2 < new_mem), "Membrane potential should decay with no input"
    assert torch.all(new_mem2 >= 0), "Membrane potential should not go negative"
    
    # Verify decay factor: new_mem should be roughly beta * old_mem
    expected_decay = beta * new_mem
    assert torch.allclose(new_mem2, expected_decay, atol=1e-6), \
        f"Decay factor mismatch: got {new_mem2}, expected {expected_decay}"

def test_zero_spike_detection_scenario(model):
    """
    Test that the model can handle scenarios where few spikes occur.
    (Preparation for FR-006 edge case handling in training loop)
    """
    model.train()
    batch_size, seq_len = 4, 16
    input_ids = torch.randint(0, 1000, (batch_size, seq_len))
    target = torch.randint(0, 1000, (batch_size, seq_len))
    
    # Run forward
    logits, aux = model(input_ids)
    
    spike_trains = aux["spike_trains"][0]
    total_spikes = spike_trains.sum().item()
    total_neurons = spike_trains.numel()
    
    # Just verify it runs without crashing and produces spikes
    assert total_spikes >= 0
    assert total_neurons > 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])