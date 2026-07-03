"""
Tests for the training loop, verifying CPU execution and early stopping logic.
"""
import torch
import torch.nn as nn
import pytest
import os
import sys
import tempfile
import time
import pandas as pd
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

# Import from project modules
from models.baseline_transformer import create_baseline_model
from metrics.perplexity import compute_perplexity
from metrics.energy_logger import EnergyLogger, EnergyRecord

# Configuration dataclass
@dataclass
class TrainingConfig:
    batch_size: int = 32
    learning_rate: float = 1e-3
    max_epochs: int = 10
    patience: int = 2
    delta: float = 0.01
    seed: int = 42
    use_cpu: bool = True

@dataclass
class MetricRecord:
    seed: int
    epoch: int
    perplexity: float
    energy_per_token_kWh: float
    wall_clock_time: float

def create_dummy_dataloader(num_samples: int = 100, seq_len: int = 64, batch_size: int = 32):
    """
    Creates a dummy dataloader for testing purposes.
    """
    dataset = torch.utils.data.TensorDataset(
        torch.randint(0, 1000, (num_samples, seq_len)),
        torch.randint(0, 1000, (num_samples, seq_len))
    )
    return torch.utils.data.DataLoader(dataset, batch_size=batch_size, shuffle=False)

class EarlyStopping:
    """
    Early stopping logic to stop training when validation loss stops improving.
    """
    def __init__(self, patience: int = 2, delta: float = 0.01):
        self.patience = patience
        self.delta = delta
        self.best_loss = None
        self.counter = 0
        self.early_stop = False

    def __call__(self, val_loss: float) -> bool:
        if self.best_loss is None:
            self.best_loss = val_loss
            return False

        if val_loss < self.best_loss - self.delta:
            self.best_loss = val_loss
            self.counter = 0
            return False
        else:
            self.counter += 1
            if self.counter >= self.patience:
                self.early_stop = True
                return True
        return False

def train_step(model: nn.Module, dataloader: torch.utils.data.DataLoader,
               optimizer: torch.optim.Optimizer, criterion: nn.Module,
               device: torch.device) -> float:
    """
    Single training step.
    """
    model.train()
    total_loss = 0.0
    num_batches = 0

    for inputs, targets in dataloader:
        inputs = inputs.to(device)
        targets = targets.to(device)

        optimizer.zero_grad()
        outputs = model(inputs)
        # Flatten for loss calculation
        outputs = outputs.view(-1, outputs.size(-1))
        targets = targets.view(-1)

        loss = criterion(outputs, targets)
        loss.backward()
        optimizer.step()

        total_loss += loss.item()
        num_batches += 1

    return total_loss / num_batches

def validate_step(model: nn.Module, dataloader: torch.utils.data.DataLoader,
                  criterion: nn.Module, device: torch.device) -> float:
    """
    Single validation step.
    """
    model.eval()
    total_loss = 0.0
    num_batches = 0

    with torch.no_grad():
        for inputs, targets in dataloader:
            inputs = inputs.to(device)
            targets = targets.to(device)

            outputs = model(inputs)
            outputs = outputs.view(-1, outputs.size(-1))
            targets = targets.view(-1)

            loss = criterion(outputs, targets)
            total_loss += loss.item()
            num_batches += 1

    return total_loss / num_batches

def run_training_loop(config: TrainingConfig, model: nn.Module,
                      train_loader: torch.utils.data.DataLoader,
                      val_loader: torch.utils.data.DataLoader,
                      output_csv_path: Optional[str] = None) -> List[MetricRecord]:
    """
    Runs the full training loop with early stopping.
    """
    device = torch.device("cpu" if config.use_cpu else "cuda")
    model = model.to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=config.learning_rate)
    criterion = nn.CrossEntropyLoss()

    early_stopper = EarlyStopping(patience=config.patience, delta=config.delta)
    records = []
    energy_logger = EnergyLogger()

    start_time = time.time()

    for epoch in range(1, config.max_epochs + 1):
        train_loss = train_step(model, train_loader, optimizer, criterion, device)
        val_loss = validate_step(model, val_loader, criterion, device)
        perplexity = compute_perplexity(val_loss)

        # Energy logging (mocked for test speed, but structure is real)
        energy_logger.start_epoch()
        time.sleep(0.01) # Simulate epoch time
        energy_record = energy_logger.end_epoch(epoch=epoch)

        # Calculate wall clock time for this epoch
        epoch_time = time.time() - start_time

        record = MetricRecord(
            seed=config.seed,
            epoch=epoch,
            perplexity=perplexity,
            energy_per_token_kWh=energy_record.energy_per_token_kWh,
            wall_clock_time=epoch_time
        )
        records.append(record)

        # Log to CSV if path provided
        if output_csv_path:
            df = pd.DataFrame([r.__dict__ for r in records])
            df.to_csv(output_csv_path, index=False)

        # Early stopping check
        if early_stopper(val_loss):
            break

    return records

# --- Test Functions ---

def test_cpu_execution_enforcement():
    """
    Verify that the training loop enforces CPU execution when specified.
    """
    config = TrainingConfig(use_cpu=True, batch_size=4, max_epochs=1)
    model = create_baseline_model(vocab_size=1000, d_model=16, nhead=2, num_layers=1)
    train_loader = create_dummy_dataloader(num_samples=16, seq_len=8, batch_size=4)
    val_loader = create_dummy_dataloader(num_samples=16, seq_len=8, batch_size=4)

    # Ensure model is on CPU
    assert next(model.parameters()).device.type == 'cpu'

    # Run a single epoch
    records = run_training_loop(config, model, train_loader, val_loader)

    # Verify that all operations happened on CPU
    for param in model.parameters():
        assert param.device.type == 'cpu', "Model parameters must be on CPU"

    assert len(records) == 1, "Should have recorded one epoch"

def test_early_stopping_logic():
    """
    Verify early stopping triggers when validation loss plateaus.
    """
    config = TrainingConfig(patience=2, delta=0.01, max_epochs=10, use_cpu=True)
    model = create_baseline_model(vocab_size=1000, d_model=16, nhead=2, num_layers=1)
    train_loader = create_dummy_dataloader(num_samples=16, seq_len=8, batch_size=4)
    val_loader = create_dummy_dataloader(num_samples=16, seq_len=8, batch_size=4)

    # Mock a scenario where loss plateaus after 3 epochs
    # We will monkey-patch the validate_step to return increasing losses
    original_validate = validate_step
    loss_sequence = [2.0, 1.5, 1.6, 1.65] # Improvement then plateau
    counter = [0]

    def mock_validate(model, loader, criterion, device):
        idx = counter[0] % len(loss_sequence)
        counter[0] += 1
        return loss_sequence[idx]

    # Temporarily replace validate_step
    import tests.test_training_loop as module
    module.validate_step = mock_validate

    try:
        records = run_training_loop(config, model, train_loader, val_loader)
        # Should stop after patience (2) epochs of no improvement
        # Improvement at epoch 1 (2.0 -> 1.5). No improvement at 2 (1.5->1.6), 3 (1.6->1.65).
        # Patience=2 means stop after 2 failures. So it should run 1 (improve), 2 (fail), 3 (fail) -> stop.
        # Total epochs: 3
        assert len(records) == 3, f"Expected 3 epochs due to early stopping, got {len(records)}"
    finally:
        module.validate_step = original_validate

def test_spiking_model_cpu_compatibility():
    """
    Verify that the spiking model can run on CPU without errors.
    """
    from models.spiking_transformer import create_spiking_model

    config = TrainingConfig(use_cpu=True, batch_size=4, max_epochs=1)
    model = create_spiking_model(vocab_size=1000, d_model=16, nhead=2, num_layers=1)
    train_loader = create_dummy_dataloader(num_samples=16, seq_len=8, batch_size=4)
    val_loader = create_dummy_dataloader(num_samples=16, seq_len=8, batch_size=4)

    # Ensure model is on CPU
    assert next(model.parameters()).device.type == 'cpu'

    # Run a single epoch
    records = run_training_loop(config, model, train_loader, val_loader)

    # Verify CPU execution
    for param in model.parameters():
        assert param.device.type == 'cpu', "Spiking model parameters must be on CPU"

    assert len(records) == 1, "Should have recorded one epoch"