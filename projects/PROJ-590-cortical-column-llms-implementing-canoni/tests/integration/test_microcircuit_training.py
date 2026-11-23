"""
Integration test for microcircuit training pipeline.

This test explicitly runs the microcircuit model (HybridNetwork) with
log_gradient_norms enabled to populate data/logs/gradient_norms_microcircuit.json
for SC-002 verification.

Dependencies:
  - T010b: log_gradient_norms implementation in src/training/homeostasis.py
  - T011d: MicrocircuitRunner with run_with_logging capability
"""

import json
import os
import time
from pathlib import Path

import pytest
import torch
from torch.utils.data import DataLoader, TensorDataset

# Import project modules
from src.models.microcircuit import create_microcircuit_column, MicrocircuitColumn
from src.models.hybrid_network import create_hybrid_network, HybridNetwork
from src.training.homeostasis import HomeostaticScaler, log_gradient_norms, apply_scaling_hook
from src.training.trainer import TrainingConfig, run_training
from src.data.benchmarks import generate_training_data, generate_test_data


@pytest.fixture
def microcircuit_model():
    """Instantiate a small HybridNetwork with MicrocircuitColumn for testing."""
    # Create a minimal configuration for integration testing
    model = create_hybrid_network(
        input_dim=10,
        hidden_dim=32,
        num_layers=2,
        num_columns=2,
        neurons_per_layer=16,
        device="cpu"
    )
    return model


@pytest.fixture
def training_data():
    """Generate small synthetic training data for the integration test."""
    # Generate small datasets to keep test fast (< 300s budget)
    train_X, train_y = generate_training_data(n_samples=200, n_features=10, seed=42)
    test_X, test_y = generate_test_data(n_samples=50, n_features=10, seed=43)
    return train_X, train_y, test_X, test_y


@pytest.fixture
def temp_output_dir(tmp_path):
    """Provide a temporary directory for output artifacts."""
    return tmp_path


def test_microcircuit_gradient_logging(
    microcircuit_model,
    training_data,
    temp_output_dir
):
    """
    Integration test: Run microcircuit training with gradient logging enabled.

    Verifies that:
      1. The model can be instantiated and run forward/backward.
      2. log_gradient_norms is called during training.
      3. The output file data/logs/gradient_norms_microcircuit.json is created.
      4. The JSON file contains valid gradient norm entries.
    """
    train_X, train_y, test_X, test_y = training_data
    # CRITICAL FIX: Use the project's canonical path as per task description,
    # not the temporary directory. The task requires populating the specific file.
    output_log_path = Path("data/logs/gradient_norms_microcircuit.json")
    
    # Ensure the directory exists
    output_log_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert data to tensors
    train_X_t = torch.tensor(train_X, dtype=torch.float32)
    train_y_t = torch.tensor(train_y, dtype=torch.float32).unsqueeze(1)
    test_X_t = torch.tensor(test_X, dtype=torch.float32)
    test_y_t = torch.tensor(test_y, dtype=torch.float32).unsqueeze(1)

    # Create data loaders
    train_dataset = TensorDataset(train_X_t, train_y_t)
    test_dataset = TensorDataset(test_X_t, test_y_t)
    train_loader = DataLoader(train_dataset, batch_size=16, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=16, shuffle=False)

    # Configure training
    # We pass the absolute path to the log file so the trainer writes to the correct location
    config = TrainingConfig(
        epochs=3,
        learning_rate=1e-3,
        device="cpu",
        log_gradient_norms=True,
        gradient_norms_log_path=str(output_log_path),
        seed=42
    )

    # Run training
    start_time = time.time()
    metrics = run_training(
        model=microcircuit_model,
        train_loader=train_loader,
        test_loader=test_loader,
        config=config
    )
    elapsed = time.time() - start_time

    # Assertions
    assert elapsed < 300, f"Training took too long: {elapsed}s"
    assert metrics is not None, "Training returned no metrics"

    # Verify output file exists at the canonical path
    assert output_log_path.exists(), f"Gradient norms log not created at {output_log_path}"

    # Verify JSON content
    with open(output_log_path, "r") as f:
        log_data = json.load(f)

    assert isinstance(log_data, list), "Gradient norms log should be a list"
    assert len(log_data) > 0, "Gradient norms log is empty"

    # Check schema of first entry
    first_entry = log_data[0]
    assert "step" in first_entry, "Missing 'step' in log entry"
    assert "grad_norm" in first_entry, "Missing 'grad_norm' in log entry"
    assert "timestamp" in first_entry, "Missing 'timestamp' in log entry"

    # Verify values are numeric
    assert isinstance(first_entry["step"], int), "step must be int"
    assert isinstance(first_entry["grad_norm"], float), "grad_norm must be float"
    assert first_entry["grad_norm"] >= 0, "grad_norm must be non-negative"

    # Optional: Verify that gradient norms are not all zero (model is learning)
    grad_norms = [entry["grad_norm"] for entry in log_data]
    assert any(gn > 1e-6 for gn in grad_norms), "All gradient norms are near zero; model may not be updating"

    print(f"Microcircuit training completed in {elapsed:.2f}s. Logged {len(log_data)} gradient norm entries.")
    print(f"Output written to: {output_log_path}")