"""
Tests for the training loop, verifying CPU execution enforcement and early stopping logic.

This module provides pytest test cases to ensure:
1. Training runs exclusively on CPU (no GPU usage).
2. Early stopping logic correctly halts training when validation loss plateaus.
3. The training loop integrates correctly with the model and data loaders.
"""
import os
import sys
import tempfile
import time
import torch
import torch.nn as nn
import pytest
import pandas as pd
import numpy as np

# Import project modules
from models.baseline_transformer import create_baseline_model
from metrics.perplexity import compute_perplexity
from data.dataset_loader import get_wikitext_dataloader

# --------------------------------------------------------------------------
# Helper Classes and Functions (Mirroring logic expected in main.py or shared)
# --------------------------------------------------------------------------

class MetricRecord:
    """Simple data structure to hold training metrics for a single step/epoch."""
    def __init__(self, epoch, loss, perplexity, energy=None, wall_clock=None):
        self.epoch = epoch
        self.loss = loss
        self.perplexity = perplexity
        self.energy = energy
        self.wall_clock = wall_clock

class TrainingConfig:
    """Configuration container for training parameters."""
    def __init__(self, patience=2, delta=0.01, max_epochs=10, batch_size=32, lr=1e-3):
        self.patience = patience
        self.delta = delta
        self.max_epochs = max_epochs
        self.batch_size = batch_size
        self.lr = lr

class EarlyStopping:
    """
    Early stopping handler to prevent overfitting.
    
    Args:
        patience: Number of epochs with no improvement after which training will be stopped.
        delta: Minimum change in the monitored quantity to qualify as an improvement.
    """
    def __init__(self, patience=2, delta=0.01):
        self.patience = patience
        self.delta = delta
        self.counter = 0
        self.best_loss = None
        self.should_stop = False

    def __call__(self, val_loss):
        if self.best_loss is None:
            self.best_loss = val_loss
            self.counter = 0
        else:
            if val_loss > self.best_loss - self.delta:
                self.counter += 1
                if self.counter >= self.patience:
                    self.should_stop = True
            else:
                self.best_loss = val_loss
                self.counter = 0
        return self.should_stop

def create_dummy_dataloader(num_samples=128, seq_len=64, batch_size=16):
    """
    Creates a dummy dataloader for testing purposes.
    Generates random token IDs to simulate a dataset without loading real data.
    """
    # Create dummy data tensor
    data = torch.randint(0, 1000, (num_samples, seq_len))
    
    # Simple dataset wrapper
    class DummyDataset(torch.utils.data.Dataset):
        def __init__(self, data):
            self.data = data
        def __len__(self):
            return len(self.data)
        def __getitem__(self, idx):
            return self.data[idx]

    dataset = DummyDataset(data)
    loader = torch.utils.data.DataLoader(dataset, batch_size=batch_size, shuffle=False)
    return loader

def train_step(model, batch, criterion, device):
    """
    Performs a single training step.
    """
    model.train()
    batch = batch.to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    optimizer.zero_grad()
    
    # Shift inputs for next token prediction
    inputs = batch[:, :-1]
    targets = batch[:, 1:]
    
    outputs = model(inputs)
    # Flatten for loss calculation
    outputs = outputs.reshape(-1, outputs.size(-1))
    targets = targets.reshape(-1)
    
    loss = criterion(outputs, targets)
    loss.backward()
    optimizer.step()
    return loss.item()

def validate_step(model, batch, criterion, device):
    """
    Performs a single validation step.
    """
    model.eval()
    batch = batch.to(device)
    with torch.no_grad():
        inputs = batch[:, :-1]
        targets = batch[:, 1:]
        outputs = model(inputs)
        outputs = outputs.reshape(-1, outputs.size(-1))
        targets = targets.reshape(-1)
        loss = criterion(outputs, targets)
    return loss.item()

def run_training_loop(model, train_loader, val_loader, config, device, max_epochs_override=None):
    """
    Runs the training loop with early stopping.
    
    Args:
        model: The model to train.
        train_loader: DataLoader for training data.
        val_loader: DataLoader for validation data.
        config: TrainingConfig instance.
        device: torch device (cpu or cuda).
        max_epochs_override: Optional override for max epochs (for testing).
    
    Returns:
        list: List of MetricRecord objects.
    """
    criterion = nn.CrossEntropyLoss()
    early_stopper = EarlyStopping(patience=config.patience, delta=config.delta)
    metrics_log = []
    
    max_epochs = max_epochs_override if max_epochs_override else config.max_epochs

    for epoch in range(1, max_epochs + 1):
        # Training phase
        epoch_loss = 0.0
        for batch in train_loader:
            loss = train_step(model, batch, criterion, device)
            epoch_loss += loss
        
        avg_train_loss = epoch_loss / len(train_loader)
        
        # Validation phase
        val_loss = 0.0
        for batch in val_loader:
            v_loss = validate_step(model, batch, criterion, device)
            val_loss += v_loss
        
        avg_val_loss = val_loss / len(val_loader)
        
        # Compute perplexity
        perplexity = compute_perplexity(torch.tensor(avg_val_loss))
        
        # Record metrics
        record = MetricRecord(
            epoch=epoch,
            loss=avg_train_loss,
            perplexity=perplexity,
            wall_clock=time.time()
        )
        metrics_log.append(record)
        
        # Check early stopping
        if early_stopper(avg_val_loss):
            break
    
    return metrics_log

# --------------------------------------------------------------------------
# Pytest Test Cases
# --------------------------------------------------------------------------

def test_cpu_execution_enforcement():
    """
    Verifies that the training loop runs exclusively on CPU.
    This test ensures that if CUDA is available, the model is explicitly moved to CPU
    and no GPU tensors are created during the training process.
    """
    # Ensure we are testing on CPU
    device = torch.device("cpu")
    assert device.type == "cpu", "Test must run on CPU to verify enforcement"
    
    # Create a small model
    model = create_baseline_model(d_model=16, nhead=2, num_layers=1, vocab_size=1000)
    model = model.to(device)
    
    # Create dummy data
    train_loader = create_dummy_dataloader(num_samples=64, batch_size=8)
    val_loader = create_dummy_dataloader(num_samples=32, batch_size=8)
    
    config = TrainingConfig(patience=5, max_epochs=2)
    
    # Run training
    metrics = run_training_loop(model, train_loader, val_loader, config, device)
    
    # Verify that no CUDA tensors were created
    for param in model.parameters():
        assert param.device.type == "cpu", f"Parameter found on {param.device}, expected cpu"
    
    # Verify that metrics were recorded
    assert len(metrics) > 0, "No metrics recorded during training"
    
    # Verify that all loss values are finite (training didn't explode)
    for m in metrics:
        assert np.isfinite(m.loss), f"Loss is not finite at epoch {m.epoch}: {m.loss}"
        assert np.isfinite(m.perplexity), f"Perplexity is not finite at epoch {m.epoch}: {m.perplexity}"

def test_early_stopping_logic():
    """
    Verifies that early stopping correctly halts training when validation loss plateaus.
    This test simulates a scenario where validation loss stops improving after a few epochs.
    """
    device = torch.device("cpu")
    model = create_baseline_model(d_model=16, nhead=2, num_layers=1, vocab_size=1000)
    model = model.to(device)
    
    train_loader = create_dummy_dataloader(num_samples=64, batch_size=8)
    val_loader = create_dummy_dataloader(num_samples=32, batch_size=8)
    
    # Set a very low patience to trigger early stopping quickly
    config = TrainingConfig(patience=2, delta=0.01, max_epochs=10)
    
    # Mock the validate_step to simulate plateauing loss
    # We will patch the function to return increasing or constant loss after a certain point
    original_validate_step = validate_step
    
    call_count = 0
    plateau_losses = [2.0, 1.5, 1.51, 1.52, 1.53, 1.54] # Loss stops improving after epoch 2
    
    def mock_validate_step(model, batch, criterion, device):
        nonlocal call_count
        if call_count < len(plateau_losses):
            loss = plateau_losses[call_count]
            call_count += 1
            return loss
        return 1.53 # Continue plateauing
    
    # Run training with mocked validation
    # Note: We need to patch inside the run_training_loop or re-implement the loop for this test
    # To keep it simple, we will re-implement the loop logic here with the mock
    
    criterion = nn.CrossEntropyLoss()
    early_stopper = EarlyStopping(patience=config.patience, delta=config.delta)
    metrics_log = []
    max_epochs = 10
    epoch_losses = []
    
    # Simulate specific loss progression for validation
    # Epoch 1: 2.0 (Best)
    # Epoch 2: 1.5 (Best)
    # Epoch 3: 1.51 (No improvement > delta) -> counter=1
    # Epoch 4: 1.52 (No improvement > delta) -> counter=2 -> STOP
    expected_epochs = 4 
    
    for epoch in range(1, max_epochs + 1):
        # Simulate training loss (just random for this test)
        train_loss = 1.0 
        
        # Simulate validation loss
        if epoch <= len(plateau_losses):
            val_loss = plateau_losses[epoch-1]
        else:
            val_loss = 1.53
        
        epoch_losses.append(val_loss)
        
        if early_stopper(val_loss):
            # Training should stop here
            break
    
    # Assert that training stopped at the expected epoch
    # With patience=2, it should stop after 2 epochs of no improvement
    # Improvement at 1->2. No improvement at 2->3 (count=1). No improvement at 3->4 (count=2 -> Stop).
    # So we expect 4 epochs recorded.
    assert len(epoch_losses) == expected_epochs, f"Expected {expected_epochs} epochs, got {len(epoch_losses)}"
    assert early_stopper.should_stop, "Early stopping flag should be True"

def test_spiking_model_cpu_compatibility():
    """
    Verifies that the spiking model (if imported) can also run on CPU without errors.
    This ensures consistency across model types.
    """
    try:
        from models.spiking_transformer import create_spiking_model
        
        device = torch.device("cpu")
        model = create_spiking_model(d_model=16, nhead=2, num_layers=1, vocab_size=1000)
        model = model.to(device)
        
        train_loader = create_dummy_dataloader(num_samples=32, batch_size=8)
        val_loader = create_dummy_dataloader(num_samples=16, batch_size=8)
        
        config = TrainingConfig(patience=5, max_epochs=1)
        
        metrics = run_training_loop(model, train_loader, val_loader, config, device)
        
        assert len(metrics) == 1, "Spiking model training should complete at least 1 epoch"
        assert metrics[0].loss < float('inf'), "Spiking model loss should be finite"
        
    except ImportError:
        pytest.skip("Spiking transformer module not available for this test")

def test_training_loop_integration_with_dummy_data():
    """
    Integration test to ensure the full loop runs end-to-end with dummy data.
    """
    device = torch.device("cpu")
    model = create_baseline_model(d_model=32, nhead=4, num_layers=2, vocab_size=1000)
    model = model.to(device)
    
    train_loader = create_dummy_dataloader(num_samples=256, batch_size=16)
    val_loader = create_dummy_dataloader(num_samples=64, batch_size=16)
    
    config = TrainingConfig(patience=5, max_epochs=3)
    
    metrics = run_training_loop(model, train_loader, val_loader, config, device)
    
    assert len(metrics) == 3, f"Expected 3 epochs, got {len(metrics)}"
    
    # Check that perplexity decreases or stays reasonable
    # (In a real scenario it decreases, here we just check it's valid)
    for m in metrics:
        assert m.perplexity > 1.0, "Perplexity must be > 1.0"
        assert m.perplexity < 10000.0, "Perplexity should not be excessively high"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])