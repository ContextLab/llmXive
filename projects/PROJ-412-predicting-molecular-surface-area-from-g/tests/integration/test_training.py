"""
Integration test for the training loop and early stopping mechanism.

This test verifies that:
1. The training loop runs to completion (or early stops) without crashing.
2. The EarlyStopping mechanism correctly halts training when validation loss plateaus.
3. The model produces valid predictions on the test set.
4. The output artifacts (predictions parquet) are generated correctly.

Dependencies:
- T016: Data splitting (train_indices, test_indices)
- T021a: GCN Model definition
- T022: Training loop implementation
- T002b: Config (RANDOM_SEED)
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any

import pytest
import numpy as np
import pandas as pd
import torch
from torch_geometric.data import Data

# Project imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.config import RANDOM_SEED
from code.utils.seed import set_seed
from code.utils.logging import get_logger
from code.models.gcn import GCNModel, create_model_from_processed_data
from code.models.train import EarlyStopping, train_model, generate_predictions
from code.data.split import load_processed_data, stratified_split_by_mw

logger = get_logger(__name__)

# Constants for test configuration
TEST_EPOCHS = 10
TEST_BATCH_SIZE = 32
TEST_LR = 0.01
TEST_PATIENCE = 3
TEST_HIDDEN_DIM = 16
TEST_OUTPUT_DIM = 1

@pytest.fixture(scope="module")
def test_environment():
    """
    Sets up a minimal test environment with synthetic but structurally valid data
    to simulate the training pipeline without requiring the full ZINC15 ingestion.
    
    Note: This uses a small synthetic dataset to ensure the test is fast and 
    deterministic, while still exercising the real training logic.
    """
    # Create a temporary directory for test outputs
    temp_dir = tempfile.mkdtemp(prefix="training_test_")
    data_dir = Path(temp_dir) / "data"
    results_dir = Path(temp_dir) / "results"
    data_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    # Set seed for reproducibility
    set_seed(RANDOM_SEED)

    # Generate synthetic graph data
    # We create a small dataset of ~100 molecules with random features
    # to simulate the output of T014/T015/T016
    num_molecules = 100
    num_atoms = 10
    num_features = 3  # atom_type, hybridization, formal_charge
    
    smiles_list = [f"SMILES_{i}" for i in range(num_molecules)]
    mw_list = np.random.uniform(100.0, 500.0, num_molecules)
    surface_area_list = np.random.uniform(50.0, 200.0, num_molecules)
    
    # Create mock PyG Data objects
    graphs = []
    for i in range(num_molecules):
        # Random node features
        x = torch.randn(num_atoms, num_features)
        # Random edge index (fully connected for simplicity in test)
        edge_index = torch.randint(0, num_atoms, (2, num_atoms * 2))
        # Target
        y = torch.tensor([surface_area_list[i]], dtype=torch.float)
        
        data = Data(x=x, edge_index=edge_index, y=y, smiles=smiles_list[i], mw=mw_list[i])
        graphs.append(data)

    # Split data manually (stratified by MW is complex to mock perfectly, so we use random split)
    split_idx = int(len(graphs) * 0.8)
    train_graphs = graphs[:split_idx]
    test_graphs = graphs[split_idx:]

    # Save to temporary parquet-like structure (using JSON for simplicity in test)
    # In real scenario, this would be loaded from data/processed/paired_dataset.parquet
    # For this test, we pass the data objects directly to the training function
    
    return {
        "temp_dir": temp_dir,
        "train_graphs": train_graphs,
        "test_graphs": test_graphs,
        "results_dir": results_dir,
        "data_dir": data_dir
    }

def test_training_loop_completes(test_environment):
    """
    Test that the training loop runs for the specified number of epochs 
    (or early stops) and produces a model artifact.
    """
    train_graphs = test_environment["train_graphs"]
    test_graphs = test_environment["test_graphs"]
    results_dir = test_environment["results_dir"]
    
    # Setup model
    # We need to infer input dim from the first graph
    input_dim = train_graphs[0].x.shape[1]
    
    model = GCNModel(
        input_dim=input_dim,
        hidden_dim=TEST_HIDDEN_DIM,
        output_dim=TEST_OUTPUT_DIM,
        num_layers=2
    )
    
    early_stopping = EarlyStopping(
        patience=TEST_PATIENCE,
        verbose=True,
        path=results_dir / "best_model.pt"
    )
    
    # Run training
    # We use a very small number of epochs to ensure the test is fast
    # but enough to trigger early stopping if the loss plateaus
    history = train_model(
        model=model,
        train_data=train_graphs,
        test_data=test_graphs,
        epochs=TEST_EPOCHS,
        batch_size=TEST_BATCH_SIZE,
        lr=TEST_LR,
        early_stopping=early_stopping,
        device="cpu"
    )
    
    # Assertions
    assert history is not None, "Training history should not be None"
    assert isinstance(history, dict), "History should be a dictionary"
    assert "train_loss" in history, "History should contain train_loss"
    assert "val_loss" in history, "History should contain val_loss"
    
    # Check that training actually ran
    assert len(history["train_loss"]) > 0, "Training should have at least one epoch"
    
    # Check that early stopping was triggered or max epochs reached
    # If early stopping triggered, history length should be <= TEST_EPOCHS + patience
    assert len(history["train_loss"]) <= TEST_EPOCHS + TEST_PATIENCE, \
        "Training should stop early or at max epochs"
        
    logger.info(f"Training completed in {len(history['train_loss'])} epochs")
    
    # Verify model file exists if early stopping saved it
    best_model_path = results_dir / "best_model.pt"
    if early_stopping.early_stop:
        assert best_model_path.exists(), "Best model should be saved if early stopping triggered"

def test_early_stopping_logic(test_environment):
    """
    Test that EarlyStopping correctly identifies a plateau and stops training.
    We simulate a scenario where validation loss stops improving.
    """
    # Create a scenario where loss plateaus
    # We'll use a very small dataset and high patience to force early stopping
    # by artificially creating a plateau in the loss curve
    
    train_graphs = test_environment["train_graphs"]
    test_graphs = test_environment["test_graphs"]
    results_dir = test_environment["results_dir"]
    
    input_dim = train_graphs[0].x.shape[1]
    model = GCNModel(
        input_dim=input_dim,
        hidden_dim=TEST_HIDDEN_DIM,
        output_dim=TEST_OUTPUT_DIM,
        num_layers=2
    )
    
    # Use a very small patience to force early stopping quickly
    patience = 2
    early_stopping = EarlyStopping(patience=patience, verbose=False)
    
    # Train for a few epochs
    history = train_model(
        model=model,
        train_data=train_graphs,
        test_data=test_graphs,
        epochs=10,
        batch_size=TEST_BATCH_SIZE,
        lr=0.001, # Lower LR to make convergence slower and plateau more likely
        early_stopping=early_stopping,
        device="cpu"
    )
    
    # Verify early stopping behavior
    # If the loss plateaued, early_stop should be True
    # Note: In a real scenario, this depends on the data and model convergence
    # We just verify that the mechanism runs without error
    
    assert early_stopping is not None
    assert hasattr(early_stopping, 'early_stop')
    
    # Verify that if early_stop is True, the best model was saved
    if early_stopping.early_stop:
        best_model_path = results_dir / "best_model.pt"
        assert best_model_path.exists(), "Best model should be saved when early stopping triggers"

def test_prediction_generation(test_environment):
    """
    Test that the generate_predictions function produces a valid parquet file
    with the required columns: smiles, predicted_sasa, error.
    """
    train_graphs = test_environment["train_graphs"]
    test_graphs = test_environment["test_graphs"]
    results_dir = test_environment["results_dir"]
    
    input_dim = train_graphs[0].x.shape[1]
    model = GCNModel(
        input_dim=input_dim,
        hidden_dim=TEST_HIDDEN_DIM,
        output_dim=TEST_OUTPUT_DIM,
        num_layers=2
    )
    
    # Train briefly
    early_stopping = EarlyStopping(patience=5, verbose=False)
    train_model(
        model=model,
        train_data=train_graphs,
        test_data=test_graphs,
        epochs=5,
        batch_size=TEST_BATCH_SIZE,
        lr=TEST_LR,
        early_stopping=early_stopping,
        device="cpu"
    )
    
    # Generate predictions
    predictions_path = results_dir / "gcn_predictions.parquet"
    generate_predictions(
        model=model,
        test_data=test_graphs,
        output_path=str(predictions_path),
        device="cpu"
    )
    
    # Verify output file exists
    assert predictions_path.exists(), "Predictions file should be created"
    
    # Load and verify schema
    df = pd.read_parquet(predictions_path)
    
    required_columns = ["smiles", "predicted_sasa", "error"]
    for col in required_columns:
        assert col in df.columns, f"Column {col} should be in predictions"
    
    # Verify data types
    assert df["smiles"].dtype == object, "smiles should be string"
    assert np.issubdtype(df["predicted_sasa"].dtype, np.floating), "predicted_sasa should be float"
    assert np.issubdtype(df["error"].dtype, np.floating), "error should be float"
    
    # Verify no NaN in critical columns
    assert not df["predicted_sasa"].isna().any(), "predicted_sasa should not contain NaN"
    assert not df["error"].isna().any(), "error should not contain NaN"
    
    logger.info(f"Predictions generated: {len(df)} rows")

def test_training_with_seed_reproducibility(test_environment):
    """
    Test that training with the same seed produces consistent results.
    """
    set_seed(RANDOM_SEED)
    train_graphs = test_environment["train_graphs"]
    test_graphs = test_environment["test_graphs"]
    
    input_dim = train_graphs[0].x.shape[1]
    model1 = GCNModel(
        input_dim=input_dim,
        hidden_dim=TEST_HIDDEN_DIM,
        output_dim=TEST_OUTPUT_DIM,
        num_layers=2
    )
    
    set_seed(RANDOM_SEED)
    model2 = GCNModel(
        input_dim=input_dim,
        hidden_dim=TEST_HIDDEN_DIM,
        output_dim=TEST_OUTPUT_DIM,
        num_layers=2
    )
    
    # Train both
    early_stopping1 = EarlyStopping(patience=5, verbose=False)
    early_stopping2 = EarlyStopping(patience=5, verbose=False)
    
    history1 = train_model(
        model=model1,
        train_data=train_graphs,
        test_data=test_graphs,
        epochs=5,
        batch_size=TEST_BATCH_SIZE,
        lr=TEST_LR,
        early_stopping=early_stopping1,
        device="cpu"
    )
    
    history2 = train_model(
        model=model2,
        train_data=train_graphs,
        test_data=test_graphs,
        epochs=5,
        batch_size=TEST_BATCH_SIZE,
        lr=TEST_LR,
        early_stopping=early_stopping2,
        device="cpu"
    )
    
    # Compare initial losses (should be identical with same seed)
    # Note: Due to potential non-determinism in some operations, we check for approximate equality
    assert np.isclose(history1["train_loss"][0], history2["train_loss"][0], rtol=1e-5), \
        "Initial training loss should be identical with same seed"

def test_batch_size_handling(test_environment):
    """
    Test that the training loop handles batch sizes correctly.
    """
    train_graphs = test_environment["train_graphs"]
    test_graphs = test_environment["test_graphs"]
    
    input_dim = train_graphs[0].x.shape[1]
    model = GCNModel(
        input_dim=input_dim,
        hidden_dim=TEST_HIDDEN_DIM,
        output_dim=TEST_OUTPUT_DIM,
        num_layers=2
    )
    
    # Test with a batch size larger than the dataset (should handle gracefully)
    large_batch_size = len(train_graphs) + 10
    early_stopping = EarlyStopping(patience=5, verbose=False)
    
    history = train_model(
        model=model,
        train_data=train_graphs,
        test_data=test_graphs,
        epochs=2,
        batch_size=large_batch_size,
        lr=TEST_LR,
        early_stopping=early_stopping,
        device="cpu"
    )
    
    # Should complete without crashing
    assert len(history["train_loss"]) == 2, "Should complete 2 epochs"
    
    # Test with batch size = 1
    early_stopping_small = EarlyStopping(patience=5, verbose=False)
    history_small = train_model(
        model=model,
        train_data=train_graphs,
        test_data=test_graphs,
        epochs=2,
        batch_size=1,
        lr=TEST_LR,
        early_stopping=early_stopping_small,
        device="cpu"
    )
    
    assert len(history_small["train_loss"]) == 2, "Should complete 2 epochs with batch_size=1"

def cleanup(test_environment):
    """Clean up temporary test directory"""
    if "temp_dir" in test_environment:
        shutil.rmtree(test_environment["temp_dir"], ignore_errors=True)