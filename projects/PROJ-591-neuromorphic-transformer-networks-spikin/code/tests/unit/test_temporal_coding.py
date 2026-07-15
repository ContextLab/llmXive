import pytest
import torch
import numpy as np
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from metrics.temporal_coding import (
    compute_isi_variance,
    compute_bits_per_spike,
    compute_spike_train_synchrony,
    extract_spike_trains_from_model_outputs,
    analyze_spike_trains
)

@pytest.fixture
def dummy_spike_trains():
    """
    Create dummy spike trains for testing.
    Returns a list of lists of spike times (in steps).
    """
    # Neuron 0: spikes at [1, 2, 3, 5, 8] -> ISIs: [1, 1, 2, 3]
    # Neuron 1: spikes at [1, 4, 7] -> ISIs: [3, 3]
    # Neuron 2: spikes at [] (silent)
    return [
        [1, 2, 3, 5, 8],
        [1, 4, 7],
        []
    ]

@pytest.fixture
def dummy_model_output():
    """
    Create a dummy model output tensor that mimics spiking behavior.
    Shape: (batch, time_steps, hidden_dim)
    Values are 0.0 (no spike) or 1.0 (spike).
    """
    batch_size = 2
    time_steps = 10
    hidden_dim = 3
    output = torch.zeros(batch_size, time_steps, hidden_dim)
    
    # Batch 0: Neuron 0 spikes at t=1,2,3; Neuron 1 spikes at t=5; Neuron 2 silent
    output[0, 1, 0] = 1.0
    output[0, 2, 0] = 1.0
    output[0, 3, 0] = 1.0
    output[0, 5, 1] = 1.0
    
    # Batch 1: Neuron 0 spikes at t=2,4; Neuron 1 spikes at t=1,3,5; Neuron 2 spikes at t=6
    output[1, 2, 0] = 1.0
    output[1, 4, 0] = 1.0
    output[1, 1, 1] = 1.0
    output[1, 3, 1] = 1.0
    output[1, 5, 1] = 1.0
    output[1, 6, 2] = 1.0
    
    return output

def test_compute_isi_variance_with_real_data(dummy_spike_trains):
    """Test ISI variance calculation with known values."""
    # Neuron 0: ISIs [1, 1, 2, 3] -> mean=1.75, var=0.6875
    # Neuron 1: ISIs [3, 3] -> mean=3.0, var=0.0
    # Neuron 2: Empty list -> should return 0.0 or NaN (handled by function)
    
    variances = compute_isi_variance(dummy_spike_trains)
    
    assert len(variances) == 3
    # Check Neuron 0 variance (approx 0.6875)
    assert abs(variances[0] - 0.6875) < 1e-6
    # Check Neuron 1 variance (0.0)
    assert abs(variances[1] - 0.0) < 1e-6
    # Check Neuron 2 (silent) returns 0.0
    assert variances[2] == 0.0

def test_compute_bits_per_spike_with_real_data(dummy_spike_trains):
    """Test bits/spike calculation."""
    # Total spikes: 5 (neuron 0) + 3 (neuron 1) + 0 (neuron 2) = 8
    # Time window: 9 steps (max spike time 8, assuming 0-indexed)
    # This is a simplified test; the actual function uses entropy calculation
    
    bits = compute_bits_per_spike(dummy_spike_trains, time_steps=10)
    
    # Should return a list of floats
    assert len(bits) == 3
    assert all(isinstance(b, float) for b in bits)
    # Bits per spike should be non-negative
    assert all(b >= 0.0 for b in bits)

def test_compute_spike_train_synchrony_with_real_data(dummy_spike_trains):
    """Test spike train synchrony calculation."""
    # Neuron 0 and 1 both spike at t=1 -> synchrony should be > 0
    # Neuron 2 is silent -> synchrony with others should be 0
    
    synchrony = compute_spike_train_synchrony(dummy_spike_trains, time_steps=10)
    
    assert len(synchrony) == 3
    assert all(isinstance(s, float) for s in synchrony)
    # Synchrony should be between 0 and 1
    assert all(0.0 <= s <= 1.0 for s in synchrony)

def test_extract_spike_trains_from_model_outputs(dummy_model_output):
    """Test extraction of spike trains from model output tensor."""
    spike_trains = extract_spike_trains_from_model_outputs(dummy_model_output)
    
    assert isinstance(spike_trains, list)
    assert len(spike_trains) == 2  # Batch size
    
    # Check first batch
    assert len(spike_trains[0]) == 3  # Hidden dim
    # Neuron 0 should have spikes at [1, 2, 3]
    assert spike_trains[0][0] == [1, 2, 3]
    # Neuron 1 should have spike at [5]
    assert spike_trains[0][1] == [5]
    # Neuron 2 should be empty
    assert spike_trains[0][2] == []

def test_analyze_spike_trains_with_real_data(dummy_model_output):
    """Test full spike train analysis pipeline."""
    metrics = analyze_spike_trains(dummy_model_output, time_steps=10)
    
    assert isinstance(metrics, dict)
    assert 'isi_variance' in metrics
    assert 'bits_per_spike' in metrics
    assert 'synchrony' in metrics
    
    # Check that metrics are lists of correct length
    assert len(metrics['isi_variance']) == 2  # Batch size
    assert len(metrics['bits_per_spike']) == 2
    assert len(metrics['synchrony']) == 2
    
    # Check that values are numeric
    for i in range(2):
        assert all(isinstance(v, (int, float)) for v in metrics['isi_variance'][i])
        assert all(isinstance(v, (int, float)) for v in metrics['bits_per_spike'][i])
        assert all(isinstance(v, (int, float)) for v in metrics['synchrony'][i])

def test_empty_spike_trains():
    """Test handling of completely silent neurons."""
    silent_trains = [[], [], []]
    
    variances = compute_isi_variance(silent_trains)
    assert all(v == 0.0 for v in variances)
    
    bits = compute_bits_per_spike(silent_trains, time_steps=10)
    assert all(b == 0.0 for b in bits)
    
    synchrony = compute_spike_train_synchrony(silent_trains, time_steps=10)
    assert all(s == 0.0 for s in synchrony)

def test_single_spike_trains():
    """Test handling of neurons with only one spike (no ISI)."""
    single_spike_trains = [[5], [3], [10]]
    
    variances = compute_isi_variance(single_spike_trains)
    # Single spike -> no ISI -> variance should be 0.0
    assert all(v == 0.0 for v in variances)

def test_extract_spike_trains_empty_tensor():
    """Test extraction from empty tensor."""
    empty_output = torch.zeros(1, 5, 2)
    spike_trains = extract_spike_trains_from_model_outputs(empty_output)
    
    assert len(spike_trains) == 1
    assert all(len(train) == 0 for train in spike_trains[0])
    assert all(all(t == [] for t in train) for train in spike_trains)
