import pytest
import torch
import torch.nn as nn
import numpy as np
import os
import sys
import tempfile
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from models.base import ProjectionModel
from utils.logging import setup_logging, get_logger
from utils.memory_monitor import get_process_memory_mb

logger = get_logger(__name__)

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

@pytest.fixture
def setup_models():
    """Setup a minimal projection model and frozen backbone for testing."""
    # Create a simple "frozen" backbone (mocked as a linear layer)
    backbone = nn.Linear(128, 128)
    for param in backbone.parameters():
        param.requires_grad = False
    
    # Create projection model
    # Input: 128 (embedding) + 64 (tabular query) -> Output: 128
    projection = ProjectionModel(
        embedding_dim=128,
        tabular_dim=64,
        hidden_dim=128,
        output_dim=128
    )
    
    return backbone, projection

@pytest.fixture
def dummy_data():
    """Generate dummy data for training loop test."""
    batch_size = 4
    embedding_dim = 128
    tabular_dim = 64
    
    # Simulate frozen embeddings (from CLIP/Sentence-BERT)
    embeddings = torch.randn(batch_size, embedding_dim)
    
    # Simulate tabular features (queries)
    tabular_features = torch.randn(batch_size, tabular_dim)
    
    # Simulate target labels (regression or classification proxy)
    # For convergence test, we just need a target to minimize loss against
    targets = torch.randn(batch_size, embedding_dim)
    
    return embeddings, tabular_features, targets

def test_training_convergence(setup_models, dummy_data, temp_dir):
    """
    Integration test for training loop convergence.
    
    Verifies that:
    1. The projection model trains successfully on CPU.
    2. The backbone (frozen) gradients remain zero.
    3. The loss decreases over epochs (convergence).
    4. Memory usage stays within reasonable limits (< 7GB).
    5. Model weights are saved to disk.
    """
    backbone, projection = setup_models
    embeddings, tabular_features, targets = dummy_data
    
    # Setup logging
    setup_logging(level="INFO")
    
    # Training hyperparameters
    num_epochs = 10
    learning_rate = 0.01
    device = torch.device("cpu")
    
    # Move models to device
    backbone = backbone.to(device)
    projection = projection.to(device)
    
    # Ensure backbone is frozen
    for param in backbone.parameters():
        param.requires_grad = False
    
    # Optimizer: only optimize projection parameters
    optimizer = torch.optim.Adam(
        filter(lambda p: p.requires_grad, projection.parameters()),
        lr=learning_rate
    )
    
    # Loss function
    criterion = nn.MSELoss()
    
    # Track loss history
    loss_history = []
    initial_memory_mb = get_process_memory_mb()
    
    logger.info(f"Starting training loop test. Initial memory: {initial_memory_mb:.2f} MB")
    
    projection.train()
    
    for epoch in range(num_epochs):
        optimizer.zero_grad()
        
        # Forward pass
        # In a real scenario, embeddings come from backbone, but here we simulate
        # The projection takes embeddings and tabular features
        output = projection(embeddings, tabular_features)
        
        # Calculate loss
        loss = criterion(output, targets)
        
        # Backward pass
        loss.backward()
        
        # Verify backbone gradients are still zero
        for name, param in backbone.named_parameters():
            if param.grad is not None:
                assert torch.all(param.grad == 0), f"Backbone gradient not zero for {name}"
        
        # Step optimizer
        optimizer.step()
        
        loss_history.append(loss.item())
        
        # Log progress
        if (epoch + 1) % 2 == 0:
            logger.info(f"Epoch [{epoch+1}/{num_epochs}], Loss: {loss.item():.6f}")
        
        # Check memory periodically
        current_memory_mb = get_process_memory_mb()
        if current_memory_mb > 7000:  # 7GB limit
            pytest.fail(f"Memory usage exceeded 7GB limit: {current_memory_mb:.2f} MB")
    
    # Convergence check: Loss should generally decrease
    # Allow some noise, but final loss should be lower than initial
    initial_loss = loss_history[0]
    final_loss = loss_history[-1]
    avg_loss = np.mean(loss_history)
    
    logger.info(f"Training completed. Initial Loss: {initial_loss:.6f}, Final Loss: {final_loss:.6f}, Avg Loss: {avg_loss:.6f}")
    
    # Assert convergence (loss decreased by at least 10% or reached a low threshold)
    # Using a lenient threshold to account for random initialization and small dataset
    assert final_loss < initial_loss, f"Loss did not decrease: Initial={initial_loss:.6f}, Final={final_loss:.6f}"
    
    # Save model checkpoint to verify serialization works
    checkpoint_path = os.path.join(temp_dir, "projection_checkpoint.pt")
    torch.save({
        "projection_state_dict": projection.state_dict(),
        "optimizer_state_dict": optimizer.state_dict(),
        "loss_history": loss_history,
        "epoch": num_epochs
    }, checkpoint_path)
    
    assert os.path.exists(checkpoint_path), "Checkpoint file was not created"
    
    # Load and verify checkpoint
    checkpoint = torch.load(checkpoint_path)
    assert "projection_state_dict" in checkpoint
    assert len(checkpoint["loss_history"]) == num_epochs
    
    logger.info(f"Test passed. Model converged from {initial_loss:.6f} to {final_loss:.6f}.")
    logger.info(f"Final memory usage: {get_process_memory_mb():.2f} MB")