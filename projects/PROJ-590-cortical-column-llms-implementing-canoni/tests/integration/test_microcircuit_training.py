"""
Integration test for Microcircuit Training Pipeline (US2).

This test explicitly runs the microcircuit model with `log_gradient_norms` enabled
to populate `data/logs/gradient_norms_microcircuit.json` for SC-002 verification.

Dependencies:
- T008b: log_gradient_norms function in src/training/homeostasis.py
- T007a/T007c: Microcircuit model definitions in src/models/microcircuit.py
- T022: Microcircuit runner infrastructure (conceptually)
"""
import os
import sys
import json
import tempfile
import logging
from pathlib import Path
from typing import Dict, Any

import pytest
import torch
import torch.nn as nn
import torch.optim as optim

# Add project root to path if running standalone
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from src.models.microcircuit import MicrocircuitColumn, create_microcircuit_column, LayerConfig
from src.models.hybrid_network import HybridNetwork, create_hybrid_network
from src.training.homeostasis import log_gradient_norms, HomeostasisConfig
from src.training.trainer import TrainingConfig, run_training, calculate_mae
from src.data.benchmarks import generate_training_data, generate_test_data

# Configure logging for the test run
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants for the test
TEST_LOG_PATH = "data/logs/gradient_norms_microcircuit.json"
SEED = 42
EPOCHS = 3  # Minimal epochs for integration test speed
BATCH_SIZE = 8
HIDDEN_DIM = 32
NUM_COLUMNS = 2

def _ensure_data_dirs():
    """Ensure data/logs directory exists."""
    log_dir = Path("data/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir

def _create_microcircuit_model():
    """
    Create a small HybridNetwork using MicrocircuitColumn to ensure
    the forward pass and gradient calculation work.
    """
    # Define a minimal config for the test
    # We use create_hybrid_network which internally uses MicrocircuitColumn
    # based on the API surface provided.
    model = create_hybrid_network(
        hidden_dim=HIDDEN_DIM,
        num_columns=NUM_COLUMNS,
        num_layers=2,
        dropout=0.1
    )
    return model

def _generate_dummy_dataset():
    """
    Generate small synthetic datasets for the training loop.
    Uses the real generator functions from src.data.benchmarks.
    """
    # Generate training data (Lorenz attractor based)
    train_X, train_y = generate_training_data(
        n_samples=128,
        seed=SEED,
        noise=0.0
    )
    # Generate test data (Polynomials based)
    test_X, test_y = generate_test_data(
        n_samples=64,
        seed=SEED + 1,
        noise=0.0
    )
    return train_X, train_y, test_X, test_y

def _run_microcircuit_training_loop(model, train_X, train_y, test_X, test_y, log_path: str):
    """
    Execute a short training loop with explicit gradient logging.
    This mimics the logic in src/training/trainer.py but focuses on
    the gradient logging requirement of T012c.
    """
    device = torch.device("cpu") # Force CPU for consistency
    model.to(device)
    
    train_X = torch.tensor(train_X, dtype=torch.float32).to(device)
    train_y = torch.tensor(train_y, dtype=torch.float32).to(device)
    test_X = torch.tensor(test_X, dtype=torch.float32).to(device)
    test_y = torch.tensor(test_y, dtype=torch.float32).to(device)

    optimizer = optim.Adam(model.parameters(), lr=0.01)
    criterion = nn.MSELoss()

    # Homeostasis config for logging
    homeo_config = HomeostasisConfig(
        target_ratio=4.0,
        decay_rate=0.99,
        log_interval=1
    )

    logger.info(f"Starting microcircuit training for {EPOCHS} epochs...")
    logger.info(f"Gradient log target: {log_path}")

    for epoch in range(EPOCHS):
        model.train()
        optimizer.zero_grad()
        
        # Forward pass
        outputs = model(train_X)
        loss = criterion(outputs, train_y)
        
        # Backward pass
        loss.backward()
        
        # Explicitly call log_gradient_norms as required by T012c
        # This function is defined in T008b
        log_gradient_norms(model, step=epoch, log_file=log_path)
        
        optimizer.step()

        # Log progress
        train_mae = calculate_mae(outputs, train_y)
        logger.info(f"Epoch {epoch}: Loss={loss.item():.4f}, MAE={train_mae:.4f}")

    logger.info("Training loop completed.")
    return True

@pytest.fixture(scope="module")
def model_fixture():
    """Fixture to create the model once per test module."""
    return _create_microcircuit_model()

@pytest.fixture(scope="module")
def dataset_fixture():
    """Fixture to generate datasets once per test module."""
    return _generate_dummy_dataset()

@pytest.fixture(scope="module")
def log_path_fixture():
    """Fixture to ensure log path is correct and directory exists."""
    log_dir = _ensure_data_dirs()
    return str(Path("data/logs/gradient_norms_microcircuit.json"))

def test_microcircuit_gradient_logging(
    model_fixture, 
    dataset_fixture, 
    log_path_fixture
):
    """
    Integration Test: Verify that running the microcircuit model with
    log_gradient_norms enabled produces the required JSON file at the
    repository path `data/logs/gradient_norms_microcircuit.json`.
    
    This satisfies SC-002 verification for the microcircuit variant.
    """
    train_X, train_y, test_X, test_y = dataset_fixture
    log_path = log_path_fixture
    model = model_fixture

    # Ensure the log file does not exist before starting (clean state)
    if os.path.exists(log_path):
        os.remove(log_path)
        logger.info(f"Removed existing log file: {log_path}")

    # Run the training loop
    success = _run_microcircuit_training_loop(
        model, train_X, train_y, test_X, test_y, log_path
    )

    assert success, "Training loop failed to complete"

    # Verify the log file exists at the EXACT required path
    assert os.path.exists(log_path), (
        f"Required artifact missing: {log_path}. "
        "The test must write gradient norms to this specific repository path."
    )

    # Verify the file is not empty
    file_size = os.path.getsize(log_path)
    assert file_size > 0, f"Log file {log_path} is empty."

    # Verify the content is valid JSON with expected structure
    try:
        with open(log_path, 'r') as f:
            data = json.load(f)
        
        # Basic schema validation
        assert isinstance(data, list), "Log file content must be a list of entries."
        assert len(data) > 0, "Log file must contain at least one entry."
        
        # Check for expected keys in entries
        first_entry = data[0]
        required_keys = {'step', 'total_norm', 'param_norms'}
        assert required_keys.issubset(first_entry.keys()), (
            f"Log entry missing required keys. Found: {first_entry.keys()}"
        )

        logger.info(f"Verified log file structure at {log_path}")
        logger.info(f"Sample entry: {first_entry}")
        
    except json.JSONDecodeError as e:
        pytest.fail(f"Log file {log_path} is not valid JSON: {e}")

    logger.info("Test PASSED: Gradient norms successfully logged to repository path.")

if __name__ == "__main__":
    # Allow running as a script for manual verification
    pytest.main([__file__, "-v", "-s"])
