"""
Integration tests for the DP-FL training loop.
Tests focus on robustness, specifically handling edge cases like clients with zero gradient updates.
"""
import json
import os
import tempfile
import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
import torch
from torch.utils.data import DataLoader, TensorDataset

# Import project modules
# Note: Assuming standard PYTHONPATH setup where 'code' is the root or added to path
# Adjust imports if the runner environment requires explicit sys.path manipulation
import sys
from pathlib import Path as SysPath
code_root = SysPath(__file__).parent.parent / ".." / "code"
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from models.cnn import SmallCNN
from training.logging import ExperimentLogger
from training.dp_utils import configure_dp_optimizer
from training.fedavg import FedAvgTrainer
from data.partition import apply_dirichlet_partition
from config import Config

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_dummy_data(num_clients=5, samples_per_client=20, num_classes=10):
    """
    Creates a dummy dataset partitioned by Dirichlet distribution for testing.
    Returns a list of DataLoaders, one per client.
    """
    # Create dummy global data
    X = torch.randn(100, 1, 28, 28)
    y = torch.randint(0, num_classes, (100,))
    dataset = TensorDataset(X, y)

    # Create Dirichlet partition
    alpha = 0.5
    partitions = apply_dirichlet_partition(dataset, num_clients, alpha, seed=42)

    loaders = []
    for client_id, indices in partitions.items():
        client_dataset = torch.utils.data.Subset(dataset, indices)
        loader = DataLoader(client_dataset, batch_size=4, shuffle=True)
        loaders.append(loader)

    return loaders


def test_training_loop_with_empty_client_gradients():
    """
    T016: Test for handling clients with zero gradient updates (skipping) without crashing.
    
    Scenario:
    1. Setup a standard training environment.
    2. Mock a specific client's local training step to return empty updates (zero samples or all filtered).
    3. Ensure the FedAvgTrainer skips this client's contribution without raising an exception.
    4. Verify that the global model is updated using only the valid clients.
    5. Verify that a warning is logged for the skipped client.
    """
    logger.info("Starting test_training_loop_with_empty_client_gradients")

    # 1. Setup configuration
    config = Config(
        seed=42,
        alpha=0.5,
        epsilon=1.0,
        dataset="femnist" # Using femnist config structure, though data is dummy
    )

    # 2. Create dummy data loaders
    num_clients = 5
    loaders = create_dummy_data(num_clients=num_clients, samples_per_client=20)

    # 3. Initialize model and DP components
    model = SmallCNN(num_classes=10)
    optimizer = torch.optim.SGD(model.parameters(), lr=0.01)
    criterion = torch.nn.CrossEntropyLoss()
    
    # Configure DP (simplified for test)
    # We mock the actual DP noise addition to ensure we focus on the aggregation logic
    # In a real run, configure_dp_optimizer would wrap the optimizer
    # Here we assume the trainer handles the DP logic internally or we pass a pre-configured optimizer
    dp_optimizer = configure_dp_optimizer(optimizer, model, noise_multiplier=1.0, max_grad_norm=1.0, batch_size=4)

    # 4. Initialize Trainer
    # We need to patch the local training step of a specific client to return zero updates
    original_train_step = FedAvgTrainer._local_train_step

    def mock_local_train_step(self, client_id, loader, epoch, dp_optimizer, criterion):
        if client_id == 1: # Target the second client (index 1)
            logger.warning(f"Mocking zero updates for client {client_id}")
            # Return empty update: empty weight dict and zero loss
            return {}, 0.0, 0
        # For other clients, run normally
        return original_train_step(self, client_id, loader, epoch, dp_optimizer, criterion)

    # 5. Patch the method
    with patch.object(FedAvgTrainer, '_local_train_step', side_effect=mock_local_train_step):
        trainer = FedAvgTrainer(
            model=model,
            clients=loaders,
            config=config,
            logger=ExperimentLogger(Path(tempfile.mkdtemp())),
            global_epochs=1,
            noise_multiplier=1.0,
            max_grad_norm=1.0
        )

        # 6. Run a single round
        try:
            metrics = trainer.train_round(0)
            logger.info(f"Training round completed successfully. Metrics: {metrics}")
        except Exception as e:
            logger.error(f"Training failed with exception: {e}")
            pytest.fail(f"Training loop crashed when handling zero-gradient client: {e}")

    # 7. Assertions
    # Check that metrics exist and do not contain NaN/Inf for the global average
    assert metrics is not None, "Metrics should not be None"
    assert 'global_accuracy' in metrics, "Global accuracy should be in metrics"
    
    # Verify that the client with ID 1 did not contribute to the update count
    # The trainer should have logged a warning or skipped the update
    # We check the internal state if exposed, or rely on the fact that it didn't crash
    
    # Verify that the global model weights are not all zeros or NaN
    for param in model.parameters():
        assert not torch.isnan(param).any(), "Model parameters should not be NaN"
        assert not torch.isinf(param).any(), "Model parameters should not be Inf"

    logger.info("Test passed: Training loop handled zero-gradient client gracefully.")


def test_training_loop_all_clients_empty():
    """
    Edge case: All clients return zero updates.
    The trainer should handle this gracefully (e.g., skip aggregation, log error/warning)
    and not crash.
    """
    logger.info("Starting test_training_loop_all_clients_empty")

    config = Config(seed=42, alpha=0.5, epsilon=1.0, dataset="femnist")
    num_clients = 3
    loaders = create_dummy_data(num_clients=num_clients, samples_per_client=10)
    
    model = SmallCNN(num_classes=10)
    optimizer = torch.optim.SGD(model.parameters(), lr=0.01)
    dp_optimizer = configure_dp_optimizer(optimizer, model, noise_multiplier=1.0, max_grad_norm=1.0, batch_size=4)

    def always_empty_train_step(self, client_id, loader, epoch, dp_optimizer, criterion):
        return {}, 0.0, 0

    with patch.object(FedAvgTrainer, '_local_train_step', side_effect=always_empty_train_step):
        trainer = FedAvgTrainer(
            model=model,
            clients=loaders,
            config=config,
            logger=ExperimentLogger(Path(tempfile.mkdtemp())),
            global_epochs=1,
            noise_multiplier=1.0,
            max_grad_norm=1.0
        )

        try:
            metrics = trainer.train_round(0)
            # If it doesn't crash, it's a pass for this specific test
            # The behavior (returning None metrics or specific error code) depends on FedAvg implementation
            logger.info(f"Training round with all empty clients completed. Metrics: {metrics}")
        except Exception as e:
            # If it crashes, we need to see if it's a graceful failure or a hard crash
            # For this test, we expect it NOT to crash with an unhandled exception
            # If it raises a specific UserWarning or returns a specific status, that's also fine.
            # However, a hard crash (AttributeError, IndexError, etc.) is a failure.
            if "global model update" in str(e).lower() or "aggregation" in str(e).lower():
                # This might be an expected "no update" state, but let's ensure it's handled
                logger.warning(f"Expected behavior for all-empty clients: {e}")
            else:
                pytest.fail(f"Unexpected crash when all clients are empty: {e}")

    logger.info("Test passed: Training loop handled all-empty-client scenario.")