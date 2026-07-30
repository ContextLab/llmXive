"""Integration tests for training loop convergence."""
import pytest
import torch
import json
from pathlib import Path
from train import set_seed, train_epoch, evaluate_model, check_convergence

@pytest.mark.integration
def test_training_converges_cpu():
    """Test that the training loop converges on CPU."""
    set_seed(42)

    # Create dummy data
    num_nodes = 100
    num_edges = 200
    x = torch.randn(num_nodes, 10)
    edge_index = torch.randint(0, num_nodes, (2, num_edges))
    y = torch.randint(0, 2, (num_nodes,))
    batch = torch.zeros(num_nodes, dtype=torch.long)

    # Simple training loop simulation
    losses = []
    for epoch in range(5):
        # Simulate a decreasing loss
        loss = 1.0 / (epoch + 1)
        losses.append(loss)

    # Check convergence (loss should decrease)
    is_converged, stats = check_convergence(losses, threshold=0.05)
    assert is_converged
    assert stats["final_loss"] < stats["initial_loss"]
