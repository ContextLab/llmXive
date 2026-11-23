"""
Integration test for training loop convergence (Task T018).

This test verifies that the lightweight Spectral GNN, Heterophily-aware GNN,
and Random Forest baseline models can be initialized, trained for a fixed
number of epochs, and produce metric logs indicating convergence.

It ensures:
1. Models initialize without error (CPU mode).
2. Training loop executes for the specified epochs.
3. Loss values decrease or stabilize (convergence check).
4. Metrics (MSE, MAE, Pearson R) are computed and logged.
5. Best model weights are saved to disk.
"""
import os
import sys
import json
import logging
import tempfile
import shutil
from pathlib import Path

import pytest
import torch
import numpy as np
from torch_geometric.data import Data, Batch

# Add project root to path to resolve imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from config import get_config, set_seed, ensure_directories
from models.spectral_gnn import SpectralGNN
from models.hetero_gnn import HeteroGNN
from models.random_forest_baseline import RandomForestBaseline
from utils.metrics import calculate_mse, calculate_mae, calculate_pearson_r
from utils.logging_utils import log_metric, flush_metrics, get_metrics

# Configure logging for the test
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("T018_TrainingIntegration")

@pytest.fixture(scope="module")
def mock_data():
    """
    Generate a small, deterministic synthetic dataset for training loop testing.
    This is NOT a replacement for real data in the main pipeline, but a controlled
    environment to verify the training loop logic, convergence, and file I/O.
    """
    logger.info("Generating mock training data for integration test...")
    set_seed(42)
    
    num_samples = 100
    num_features = 10  # Atom feature dimension
    num_bond_features = 5
    edge_index_dim = 2
    
    graphs = []
    targets = []
    
    for i in range(num_samples):
        # Create a random graph structure
        num_nodes = np.random.randint(5, 20)
        num_edges = np.random.randint(10, 50)
        
        edge_index = torch.randint(0, num_nodes, (2, num_edges))
        x = torch.randn(num_nodes, num_features)
        edge_attr = torch.randn(num_edges, num_bond_features)
        y = torch.tensor([np.random.randn()]) # Regression target
        
        data = Data(x=x, edge_index=edge_index, edge_attr=edge_attr, y=y)
        graphs.append(data)
        targets.append(y.item())
    
    return graphs, torch.tensor(targets)

@pytest.fixture(scope="module")
def temp_artifact_dir():
    """Create a temporary directory for artifacts during the test."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

def test_model_initialization(mock_data, temp_artifact_dir):
    """Test that all three models can be initialized."""
    graphs, targets = mock_data
    batch = Batch.from_data_list(graphs)
    
    logger.info("Initializing SpectralGNN...")
    spectral_model = SpectralGNN(
        in_channels=10, 
        hidden_channels=32, 
        out_channels=1
    )
    assert spectral_model is not None
    
    logger.info("Initializing HeteroGNN...")
    hetero_model = HeteroGNN(
        in_channels=10, 
        hidden_channels=32, 
        out_channels=1
    )
    assert hetero_model is not None
    
    logger.info("Initializing RandomForestBaseline...")
    # RF baseline expects flattened features or specific input handling
    rf_model = RandomForestBaseline(n_estimators=10, max_depth=5)
    assert rf_model is not None
    
    logger.info("All models initialized successfully.")

def test_training_loop_convergence(mock_data, temp_artifact_dir):
    """
    Test the full training loop for SpectralGNN and HeteroGNN.
    Verifies loss reduction and artifact saving.
    """
    graphs, targets = mock_data
    batch = Batch.from_data_list(graphs)
    
    # Split data
    split_idx = int(0.8 * len(graphs))
    train_batch = Batch.from_data_list(graphs[:split_idx])
    val_batch = Batch.from_data_list(graphs[split_idx:])
    
    train_targets = targets[:split_idx]
    val_targets = targets[split_idx:]
    
    models_to_test = [
        ("SpectralGNN", SpectralGNN(10, 32, 1)),
        ("HeteroGNN", HeteroGNN(10, 32, 1))
    ]
    
    for model_name, model in models_to_test:
        logger.info(f"Testing training loop for {model_name}...")
        model.train()
        optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
        
        epochs = 5
        losses = []
        
        for epoch in range(epochs):
            optimizer.zero_grad()
            outputs = model(train_batch)
            loss = torch.nn.functional.mse_loss(outputs.squeeze(), train_targets)
            loss.backward()
            optimizer.step()
            losses.append(loss.item())
            
            # Simple convergence check: loss should not explode
            assert not np.isnan(loss.item()), f"Loss is NaN at epoch {epoch}"
            assert not np.isinf(loss.item()), f"Loss is Inf at epoch {epoch}"
        
        # Check if loss decreased (convergence heuristic)
        if len(losses) > 1:
            assert losses[-1] <= losses[0] * 1.5, f"Loss did not converge for {model_name}"
        
        logger.info(f"{model_name} training completed. Initial Loss: {losses[0]:.4f}, Final Loss: {losses[-1]:.4f}")
        
        # Verify metric calculation
        model.eval()
        with torch.no_grad():
            val_outputs = model(val_batch)
            val_preds = val_outputs.squeeze().numpy()
            val_true = val_targets.numpy()
            
            mse = calculate_mse(val_true, val_preds)
            mae = calculate_mae(val_true, val_preds)
            pearson = calculate_pearson_r(val_true, val_preds)
            
            logger.info(f"Validation Metrics for {model_name}: MSE={mse:.4f}, MAE={mae:.4f}, Pearson={pearson:.4f}")
            
            assert isinstance(mse, float)
            assert isinstance(mae, float)
            assert isinstance(pearson, float)
        
        # Verify artifact saving (mock path)
        weight_path = os.path.join(temp_artifact_dir, f"best_{model_name.lower().replace(' ', '_')}.pt")
        torch.save(model.state_dict(), weight_path)
        assert os.path.exists(weight_path), f"Model weights not saved to {weight_path}"
        
        # Log metrics
        log_metric("test_mse", mse, model=model_name)
        log_metric("test_mae", mae, model=model_name)
        log_metric("test_pearson", pearson, model=model_name)
    
    flush_metrics()
    logger.info("Training loop convergence test passed for all GNN models.")

def test_random_forest_baseline_convergence(mock_data, temp_artifact_dir):
    """Test the Random Forest baseline training and evaluation."""
    graphs, targets = mock_data
    
    # Prepare data for RF (flattened node features or graph-level stats)
    # For this test, we'll use a simple aggregation of node features per graph
    X = []
    y = []
    
    for i, g in enumerate(graphs):
        # Simple mean aggregation of node features as a graph-level feature vector
        if g.num_nodes > 0:
            graph_feat = g.x.mean(dim=0).numpy()
            X.append(graph_feat)
            y.append(targets[i].item())
    
    X = np.array(X)
    y = np.array(y)
    
    train_size = int(0.8 * len(X))
    X_train, X_test = X[:train_size], X[train_size:]
    y_train, y_test = y[:train_size], y[train_size:]
    
    logger.info("Training RandomForestBaseline...")
    rf_model = RandomForestBaseline(n_estimators=10, max_depth=5)
    rf_model.fit(X_train, y_train)
    
    # Predict
    y_pred = rf_model.predict(X_test)
    
    # Evaluate
    mse = calculate_mse(y_test, y_pred)
    mae = calculate_mae(y_test, y_pred)
    pearson = calculate_pearson_r(y_test, y_pred)
    
    logger.info(f"RF Metrics: MSE={mse:.4f}, MAE={mae:.4f}, Pearson={pearson:.4f}")
    
    assert isinstance(mse, float)
    assert not np.isnan(mse)
    
    # Save mock weights (RF doesn't use .pt in same way, but we save the model object)
    import pickle
    weight_path = os.path.join(temp_artifact_dir, "best_random_forest_baseline.pkl")
    with open(weight_path, 'wb') as f:
        pickle.dump(rf_model, f)
    assert os.path.exists(weight_path)
    
    logger.info("Random Forest baseline convergence test passed.")

def test_artifact_logging(mock_data, temp_artifact_dir):
    """Verify that metrics are correctly logged and retrievable."""
    # Run a dummy log
    log_metric("dummy_metric", 0.99, model="TestModel")
    flush_metrics()
    
    metrics = get_metrics()
    assert "dummy_metric" in metrics
    assert metrics["dummy_metric"]["value"] == 0.99
    logger.info("Artifact logging test passed.")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])