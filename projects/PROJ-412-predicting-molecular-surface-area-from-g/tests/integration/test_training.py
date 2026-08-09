"""
Integration test for the GCN training loop and early stopping mechanism.

This test verifies that:
1. The training loop executes successfully with a small subset of data.
2. Early stopping triggers correctly when validation loss stops improving.
3. The model artifacts are saved to the expected location.
4. Predictions are generated and saved to the expected Parquet file.

Dependencies:
- code/models/gcn.py (GCNModel)
- code/models/train.py (train_model, EarlyStopping, load_processed_graphs)
- code/data/preprocess.py (for generating test data if needed, though we mock here)
- code/utils/seed.py (for reproducibility)
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any

import pytest
import torch
import pandas as pd
import numpy as np
from torch_geometric.data import Data

# Add project root to path if not already present
PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from code.models.gcn import GCNModel
from code.models.train import train_model, EarlyStopping, load_processed_graphs
from code.utils.seed import set_seed
from code.utils.logging import setup_logging, get_logger
from code.config import TIME_BUDGET, MAX_RAM_GB, SENSITIVITY_THRESHOLDS


# --- Fixtures ---

@pytest.fixture(scope="module")
def test_environment():
    """
    Sets up a temporary directory for test outputs and ensures the
    necessary directory structure exists for the training script.
    """
    # Create a temporary directory for this test run
    temp_dir = tempfile.mkdtemp(prefix="test_training_")
    test_artifacts_dir = Path(temp_dir) / "results" / "predictions"
    test_artifacts_dir.mkdir(parents=True, exist_ok=True)

    # Mock config values if they don't exist in the real config
    # (Though T002-Config should have created code/config.py)
    # We rely on the real config.py being present as per T002-Config completion.

    yield {
        "temp_dir": Path(temp_dir),
        "artifacts_dir": test_artifacts_dir,
    }

    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture(scope="module")
def dummy_graph_data():
    """
    Generates a small, synthetic set of PyTorch Geometric Data objects
    to simulate the output of load_processed_graphs for integration testing.
    This avoids the need to run the full ingestion/preprocessing pipeline (T048-T015)
    just to test the training loop logic.
    """
    set_seed(42)
    graphs = []
    labels = []
    smiles_list = []

    # Generate 50 dummy molecules
    num_molecules = 50
    for i in range(num_molecules):
        # Random node features (e.g., atom type, hybridization, charge)
        # Shape: [num_nodes, num_features]
        num_nodes = np.random.randint(5, 20)
        num_features = 10  # Arbitrary feature dimension
        x = torch.randn(num_nodes, num_features)

        # Random edge indices (undirected graph)
        num_edges = num_nodes * 2
        edge_index = torch.randint(0, num_nodes, (2, num_edges))

        # Create Data object
        data = Data(x=x, edge_index=edge_index)
        data.smiles = f"C{i}CC"  # Dummy SMILES
        data.target = float(i * 10.5 + np.random.normal(0, 1.0))  # Dummy SASA

        graphs.append(data)
        labels.append(data.target)
        smiles_list.append(data.smiles)

    return graphs, torch.tensor(labels, dtype=torch.float32), smiles_list


# --- Tests ---

def test_training_loop_execution_and_early_stopping(
    test_environment, dummy_graph_data
):
    """
    Integration test:
    1. Trains a GCN model on dummy data.
    2. Verifies that early stopping is triggered (since data is random/noisy).
    3. Verifies that model weights and predictions are saved.
    """
    graphs, labels, smiles_list = dummy_graph_data
    temp_dir = test_environment["temp_dir"]
    artifacts_dir = test_environment["artifacts_dir"]

    # Split data manually for the test (80/20)
    split_idx = int(len(graphs) * 0.8)
    train_data = graphs[:split_idx]
    train_labels = labels[:split_idx]
    val_data = graphs[split_idx:]
    val_labels = labels[split_idx:]

    # Create a simple DataLoader-like structure for the test
    # The train_model function expects a DataLoader or iterable of batches.
    # We will mock the DataLoader to yield these items.
    
    class DummyLoader:
        def __init__(self, data, labels, batch_size=16):
            self.data = data
            self.labels = labels
            self.batch_size = batch_size
            self.indices = list(range(len(data)))
        
        def __iter__(self):
            for i in range(0, len(self.data), self.batch_size):
                batch_data = self.data[i : i + self.batch_size]
                batch_labels = self.labels[i : i + self.batch_size]
                yield batch_data, batch_labels

        def __len__(self):
            return (len(self.data) + self.batch_size - 1) // self.batch_size

    train_loader = DummyLoader(train_data, train_labels, batch_size=8)
    val_loader = DummyLoader(val_data, val_labels, batch_size=8)

    # Setup model
    num_features = 10
    hidden_channels = 16
    model = GCNModel(num_features=num_features, hidden_channels=hidden_channels)

    # Setup early stopping
    patience = 3
    early_stopping = EarlyStopping(patience=patience, verbose=True)

    # Training parameters
    lr = 0.01
    epochs = 50
    device = "cpu"

    # Run training
    # We catch exceptions to ensure the test fails loudly if training crashes
    try:
        history = train_model(
            model=model,
            train_loader=train_loader,
            val_loader=val_loader,
            lr=lr,
            epochs=epochs,
            device=device,
            early_stopping=early_stopping,
            model_save_path=str(artifacts_dir / "gcn_model.pth"),
            predictions_save_path=str(artifacts_dir / "gcn_predictions.parquet"),
            smiles_list=smiles_list,
        )
    except Exception as e:
        pytest.fail(f"Training loop failed with exception: {e}")

    # --- Assertions ---

    # 1. Verify Early Stopping triggered
    # Since data is random, validation loss should fluctuate or increase,
    # triggering early stopping well before 50 epochs.
    assert len(history) < epochs, (
        f"Early stopping did not trigger. Training ran for {len(history)} epochs. "
        "Expected < 50 epochs due to noisy data."
    )
    assert early_stopping.early_stop, "Early stopping flag was not set to True."

    # 2. Verify Model Artifact exists
    model_path = artifacts_dir / "gcn_model.pth"
    assert model_path.exists(), f"Model artifact not saved at {model_path}"
    assert model_path.stat().st_size > 0, "Model artifact is empty."

    # 3. Verify Predictions Artifact exists
    predictions_path = artifacts_dir / "gcn_predictions.parquet"
    assert predictions_path.exists(), f"Predictions artifact not saved at {predictions_path}"

    # 4. Verify Predictions Content
    df = pd.read_parquet(predictions_path)
    required_columns = ["smiles", "predicted_sasa", "error"]
    assert list(df.columns) == required_columns, (
        f"Predictions file columns mismatch. Expected {required_columns}, got {list(df.columns)}"
    )
    assert len(df) == len(val_data), (
        f"Prediction count mismatch. Expected {len(val_data)}, got {len(df)}"
    )
    assert not df["predicted_sasa"].isna().any(), "Predictions contain NaN values."
    assert not df["error"].isna().any(), "Errors contain NaN values."

    # 5. Verify Training History
    assert "train_loss" in history, "Training history missing 'train_loss' key."
    assert "val_loss" in history, "Training history missing 'val_loss' key."
    assert len(history["train_loss"]) == len(history["val_loss"]), (
        "Train and Val history lengths mismatch."
    )

    print(f"Training completed successfully after {len(history)} epochs.")
    print(f"Early stopping triggered: {early_stopping.early_stop}")
    print(f"Best validation loss: {early_stopping.best_score}")


def test_training_with_impossible_patience(test_environment, dummy_graph_data):
    """
    Test that the training loop respects the 'max_epochs' limit even if
    early stopping hasn't triggered (e.g., if we artificially lower the
    noise to make loss decrease steadily, or just set patience high).
    """
    graphs, labels, smiles_list = dummy_graph_data
    temp_dir = test_environment["temp_dir"]
    artifacts_dir = test_environment["artifacts_dir"]

    # Use a subset for speed
    split_idx = int(len(graphs) * 0.8)
    train_data = graphs[:split_idx]
    train_labels = labels[:split_idx]
    val_data = graphs[split_idx:]
    val_labels = labels[split_idx:]

    class DummyLoader:
        def __init__(self, data, labels, batch_size=16):
            self.data = data
            self.labels = labels
            self.batch_size = batch_size
        def __iter__(self):
            for i in range(0, len(self.data), self.batch_size):
                yield self.data[i : i + self.batch_size], self.labels[i : i + self.batch_size]
        def __len__(self):
            return (len(self.data) + self.batch_size - 1) // self.batch_size

    train_loader = DummyLoader(train_data, train_labels, batch_size=8)
    val_loader = DummyLoader(val_data, val_labels, batch_size=8)

    model = GCNModel(num_features=10, hidden_channels=16)
    
    # Set patience very high so it won't trigger within max_epochs=10
    early_stopping = EarlyStopping(patience=100, verbose=True)

    max_epochs = 10
    history = train_model(
        model=model,
        train_loader=train_loader,
        val_loader=val_loader,
        lr=0.01,
        epochs=max_epochs,
        device="cpu",
        early_stopping=early_stopping,
        model_save_path=str(artifacts_dir / "gcn_model_max.pth"),
        predictions_save_path=str(artifacts_dir / "gcn_predictions_max.parquet"),
        smiles_list=smiles_list,
    )

    # Verify it ran exactly max_epochs
    assert len(history) == max_epochs, f"Expected {max_epochs} epochs, got {len(history)}"
    assert not early_stopping.early_stop, "Early stopping should not have triggered with high patience."


if __name__ == "__main__":
    pytest.main([__file__, "-v"])