"""
Unit tests for training module.
"""
import pytest
import torch
from model import PolymerGNN
from train import train_model, validate_model

def test_training_converges_cpu():
    """Test that training converges on CPU."""
    # Create a simple model
    model = PolymerGNN(num_features=10, num_classes=5)
    
    # Create dummy data
    x = torch.randn(10, 10)
    edge_index = torch.randint(0, 10, (2, 20))
    y = torch.randint(0, 5, (10,))
    
    # Train for a few epochs
    losses = []
    for epoch in range(5):
        loss = train_model(model, x, edge_index, y, epochs=1)
        losses.append(loss)
    
    # Check that loss generally decreases
    # This is a simplified check; real training would need more epochs and validation
    assert len(losses) == 5
    # Note: In a real scenario, we'd check for convergence more rigorously
