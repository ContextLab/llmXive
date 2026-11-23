"""
Integration test for training timeout functionality.
Verifies that training respects the timeout limit and exits with appropriate status.
"""
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
import time

import pytest
import torch
from torch_geometric.data import Data
import numpy as np

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.config import get_config, ensure_dirs
from models.train import train_gcn_fold, TimeoutError

@pytest.fixture
def mock_config():
    """Create a minimal config for testing timeout."""
    config = {
        'node_feature_dim': 10,
        'edge_feature_dim': 5,
        'gcn_hidden_dim': 16,
        'gcn_num_layers': 2,
        'max_epochs': 1000,
        'fold_timeout_seconds': 2,  # Very short timeout for testing
        'batch_size': 4,
        'learning_rate': 0.001,
        'patience': 5,
        'results_dir': tempfile.mkdtemp(),
        'seed': 42
    }
    return config

@pytest.fixture
def mock_graph_data():
    """Create mock graph data for testing."""
    data_list = []
    for i in range(20):
        x = torch.randn(10, 10)  # 10 nodes, 10 features
        edge_index = torch.randint(0, 10, (2, 20))
        edge_attr = torch.randn(20, 5)  # 20 edges, 5 features
        y = torch.tensor([np.random.rand()])
        data = Data(x=x, edge_index=edge_index, edge_attr=edge_attr, y=y)
        data_list.append(data)
    return data_list

def test_gcn_timeout_enforcement(mock_config, mock_graph_data, caplog):
    """Test that GCN training respects timeout and saves partial model."""
    train_data = mock_graph_data[:15]
    val_data = mock_data = mock_graph_data[15:]
    
    # Run training with very short timeout
    start_time = time.time()
    metrics = train_gcn_fold(
        train_data=train_data,
        val_data=val_data,
        fold_idx=0,
        config=mock_config,
        logger=None  # Suppress logging for this test
    )
    elapsed = time.time() - start_time
    
    # Verify timeout occurred
    assert metrics['status'] == 'timeout', f"Expected timeout but got {metrics['status']}"
    assert elapsed >= mock_config['fold_timeout_seconds'] - 0.5, f"Training took {elapsed}s, expected ~{mock_config['fold_timeout_seconds']}s"
    assert elapsed < mock_config['fold_timeout_seconds'] + 5.0, f"Training took too long: {elapsed}s"
    
    # Verify partial model was saved
    model_path = Path(mock_config['results_dir']) / 'model_artifacts' / 'gcn_fold_0_partial.pt'
    assert model_path.exists(), f"Partial model not saved at {model_path}"
    
    # Cleanup
    shutil.rmtree(mock_config['results_dir'])

def test_gcn_completion_without_timeout(mock_config, mock_graph_data):
    """Test that GCN training completes successfully when timeout is not hit."""
    # Increase timeout to allow completion
    mock_config['fold_timeout_seconds'] = 60
    mock_config['max_epochs'] = 10
    
    train_data = mock_graph_data[:15]
    val_data = mock_graph_data[15:]
    
    metrics = train_gcn_fold(
        train_data=train_data,
        val_data=val_data,
        fold_idx=1,
        config=mock_config,
        logger=None
    )
    
    # Verify successful completion
    assert metrics['status'] == 'completed', f"Expected completed but got {metrics['status']}"
    assert 'mae' in metrics
    assert 'rmse' in metrics
    assert 'r2' in metrics
    
    # Verify metrics are reasonable
    assert 0 <= metrics['mae'] <= 10, f"MAE out of range: {metrics['mae']}"
    assert 0 <= metrics['r2'] <= 1, f"R2 out of range: {metrics['r2']}"
    
    # Cleanup
    shutil.rmtree(mock_config['results_dir'])

if __name__ == '__main__':
    pytest.main([__file__, '-v'])