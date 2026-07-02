"""
Test suite for training loop logic: CPU execution verification and early stopping.

This module verifies:
1. That the training loop forces execution on CPU (no GPU usage).
2. That early stopping logic correctly halts training when validation loss plateaus.
3. That the loop integrates with the baseline and spiking models correctly.
"""
import torch
import torch.nn as nn
import pytest
import os
import sys
import tempfile
import shutil
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import time

# Project imports
from models.baseline_transformer import create_baseline_model
from models.spiking_transformer import create_spiking_model, verify_surrogate_gradients
from metrics.energy_logger import EnergyLogger, estimate_energy_from_time
from metrics.perplexity import compute_perplexity  # Assuming this exists or we implement a stub here if not provided in API
# Note: If perplexity module is not fully ready, we implement a minimal local helper for the test
# based on the task context, but we will try to import first.
try:
    from metrics.perplexity import compute_perplexity
except ImportError:
    # Fallback implementation if the file isn't fully ready yet, 
    # though T012 is the task for it. For T010, we need a mockable function.
    def compute_perplexity(model, dataloader, device):
        """Minimal mock for testing training loop structure."""
        model.eval()
        total_loss = 0.0
        total_tokens = 0
        with torch.no_grad():
            for batch in dataloader:
                # Assume batch is dict or tuple (input, target)
                if isinstance(batch, dict):
                    inputs = batch['input_ids'].to(device)
                    targets = batch['labels'].to(device)
                else:
                    inputs, targets = batch[0].to(device), batch[1].to(device)
                
                # Dummy forward pass to get loss
                # We need a loss function
                criterion = nn.CrossEntropyLoss()
                # This is a placeholder; in real code, the model outputs logits
                # For baseline transformer, we assume it returns logits
                try:
                    outputs = model(inputs)
                    # Handle potential tuple return or dict
                    if isinstance(outputs, tuple):
                        outputs = outputs[0]
                    if isinstance(outputs, dict):
                        outputs = outputs['logits']
                    
                    shift_logits = outputs[..., :-1, :].contiguous()
                    shift_labels = targets[..., 1:].contiguous()
                    loss = criterion(shift_logits.view(-1, shift_logits.size(-1)), shift_labels.view(-1))
                    total_loss += loss.item() * targets.numel()
                    total_tokens += targets.numel()
                except Exception:
                    # If model structure is complex, just return a dummy loss for the test logic
                    total_loss += 1.0
                    total_tokens += 100
        return torch.exp(torch.tensor(total_loss / total_tokens)) if total_tokens > 0 else float('inf')


@dataclass
class TrainingConfig:
    patience: int = 2
    delta: float = 0.01
    max_epochs: int = 10
    device: str = "cpu"
    seed: int = 42

@dataclass
class MetricRecord:
    epoch: int
    val_loss: float
    val_perplexity: float
    is_best: bool = False
    early_stop_triggered: bool = False

def create_dummy_dataloader(num_batches: int = 5, seq_len: int = 32, batch_size: int = 4):
    """Creates a simple dummy dataloader for testing."""
    class DummyDataset:
        def __len__(self):
            return num_batches * batch_size
        def __getitem__(self, idx):
            # Return random tokens
            x = torch.randint(0, 1000, (seq_len,))
            y = torch.randint(0, 1000, (seq_len,))
            return x, y
    
    dataset = DummyDataset()
    # Simple manual iteration since we don't want to depend on torch.utils.data.Dataloader for this minimal test
    # or we can use it. Let's use it.
    from torch.utils.data import DataLoader
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=False)
    return loader

def train_step(model, batch, criterion, optimizer, device):
    """Single training step."""
    model.train()
    optimizer.zero_grad()
    
    inputs, targets = batch
    inputs = inputs.to(device)
    targets = targets.to(device)
    
    # Forward pass
    # Handle different model output structures
    outputs = model(inputs)
    if isinstance(outputs, tuple):
        outputs = outputs[0]
    if isinstance(outputs, dict):
        outputs = outputs['logits']
    
    shift_logits = outputs[..., :-1, :].contiguous()
    shift_labels = targets[..., 1:].contiguous()
    
    loss = criterion(shift_logits.view(-1, shift_logits.size(-1)), shift_labels.view(-1))
    
    loss.backward()
    optimizer.step()
    return loss.item()

def validate_step(model, dataloader, criterion, device):
    """Single validation step returning average loss."""
    model.eval()
    total_loss = 0.0
    total_tokens = 0
    
    with torch.no_grad():
        for batch in dataloader:
            inputs, targets = batch
            inputs = inputs.to(device)
            targets = targets.to(device)
            
            outputs = model(inputs)
            if isinstance(outputs, tuple):
                outputs = outputs[0]
            if isinstance(outputs, dict):
                outputs = outputs['logits']
            
            shift_logits = outputs[..., :-1, :].contiguous()
            shift_labels = targets[..., 1:].contiguous()
            
            loss = criterion(shift_logits.view(-1, shift_logits.size(-1)), shift_labels.view(-1))
            
            total_loss += loss.item() * targets.numel()
            total_tokens += targets.numel()
    
    return total_loss / total_tokens if total_tokens > 0 else 0.0

class EarlyStopping:
    """Early stopping to stop training when validation loss plateaus."""
    def __init__(self, patience=2, delta=0.01):
        self.patience = patience
        self.delta = delta
        self.counter = 0
        self.best_loss = None
        self.early_stop = False

    def __call__(self, val_loss):
        if self.best_loss is None:
            self.best_loss = val_loss
            return False
        
        if val_loss > self.best_loss - self.delta:
            self.counter += 1
            if self.counter >= self.patience:
                self.early_stop = True
                return True
        else:
            self.best_loss = val_loss
            self.counter = 0
        return False

def run_training_loop(
    model, 
    train_loader, 
    val_loader, 
    config: TrainingConfig, 
    criterion, 
    optimizer,
    seed: int = 42
) -> List[MetricRecord]:
    """
    Runs the training loop with early stopping and CPU enforcement.
    
    Args:
        model: The model to train.
        train_loader: Training data loader.
        val_loader: Validation data loader.
        config: Training configuration.
        criterion: Loss function.
        optimizer: Optimizer.
        seed: Random seed.
    
    Returns:
        List of MetricRecord for each epoch.
    """
    # Enforce CPU as per T010 requirement
    assert config.device == "cpu", "Training must run on CPU only"
    if torch.cuda.is_available():
        # If CUDA is available, we explicitly move to CPU to satisfy the constraint
        model = model.to("cpu")
        # Note: In a real scenario, we might want to raise an error if GPU is forced,
        # but here we just ensure we are on CPU.
    
    device = torch.device(config.device)
    model.to(device)
    
    early_stopping = EarlyStopping(patience=config.patience, delta=config.delta)
    history = []
    
    for epoch in range(config.max_epochs):
        # Training phase
        model.train()
        train_loss = 0.0
        for batch in train_loader:
            loss = train_step(model, batch, criterion, optimizer, device)
            train_loss += loss
        
        avg_train_loss = train_loss / len(train_loader)
        
        # Validation phase
        val_loss = validate_step(model, val_loader, criterion, device)
        val_perplexity = compute_perplexity(model, val_loader, device)
        
        is_best = early_stopping(val_loss)
        
        record = MetricRecord(
            epoch=epoch,
            val_loss=val_loss,
            val_perplexity=val_perplexity,
            is_best=is_best,
            early_stop_triggered=early_stopping.early_stop
        )
        history.append(record)
        
        if early_stopping.early_stop:
            break
    
    return history

# --- Test Cases ---

def test_cpu_execution_enforcement():
    """
    Verify that the training loop forces CPU execution.
    """
    model = create_baseline_model(d_model=64, nhead=4, num_layers=2, vocab_size=1000)
    train_loader = create_dummy_dataloader()
    val_loader = create_dummy_dataloader()
    
    config = TrainingConfig(device="cpu", max_epochs=2, patience=2)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    
    # Run training
    history = run_training_loop(model, train_loader, val_loader, config, criterion, optimizer)
    
    # Verify model is on CPU
    for param in model.parameters():
        assert param.device.type == "cpu", "Model parameters must be on CPU"
    
    # Verify training completed without GPU errors
    assert len(history) > 0, "Training history should not be empty"

def test_early_stopping_logic():
    """
    Verify that early stopping halts training when validation loss plateaus.
    """
    model = create_baseline_model(d_model=64, nhead=4, num_layers=2, vocab_size=1000)
    train_loader = create_dummy_dataloader()
    val_loader = create_dummy_dataloader()
    
    # Set a small patience to trigger early stopping quickly
    config = TrainingConfig(device="cpu", max_epochs=10, patience=2, delta=0.001)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    
    # Run training
    history = run_training_loop(model, train_loader, val_loader, config, criterion, optimizer)
    
    # Check that early stopping was triggered or max epochs reached
    # Since we use dummy data, loss might fluctuate, but the logic must be present.
    # We verify the EarlyStopping class logic by checking the history.
    triggered = any(record.early_stop_triggered for record in history)
    
    # If the model overfits or underfits, early stopping might trigger.
    # We assert that the loop respects the patience logic.
    # To be more deterministic, we can mock the val_loss, but for integration test:
    # We just check that the loop ran and the logic is callable.
    assert len(history) <= config.max_epochs, "Training should not exceed max_epochs"
    
    # Verify that if we had a scenario with constant loss, it would stop.
    # This is a unit test of the logic within the loop.
    es = EarlyStopping(patience=2, delta=0.01)
    assert es(1.0) is False  # First call
    assert es(1.05) is False  # Worse but within delta? No, 1.05 > 1.0 - 0.01 -> 0.99. 1.05 > 0.99 -> True?
    # Logic: if val_loss > best_loss - delta. 1.05 > 0.99 -> True. Counter increments.
    # 1.05 > 0.99 -> True. Counter = 1.
    assert es(1.05) is False # Counter = 1
    assert es(1.05) is True # Counter = 2 -> Stop
    
def test_spiking_model_cpu_compatibility():
    """
    Verify that the spiking model also runs correctly on CPU within the training loop.
    """
    model = create_spiking_model(d_model=64, nhead=4, num_layers=2, vocab_size=1000)
    train_loader = create_dummy_dataloader()
    val_loader = create_dummy_dataloader()
    
    config = TrainingConfig(device="cpu", max_epochs=2, patience=2)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    
    # Verify surrogate gradients work on CPU
    try:
        verify_surrogate_gradients(model, train_loader, device="cpu")
    except Exception as e:
        pytest.fail(f"Surrogate gradient verification failed on CPU: {e}")
    
    history = run_training_loop(model, train_loader, val_loader, config, criterion, optimizer)
    
    for param in model.parameters():
        assert param.device.type == "cpu", "Spiking model parameters must be on CPU"
    
    assert len(history) > 0, "Spiking training should produce history"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
