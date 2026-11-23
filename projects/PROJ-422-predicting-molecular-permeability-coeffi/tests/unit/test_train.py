"""
Unit tests for the training module.
"""
import pytest
import numpy as np
import pandas as pd
import torch
from pathlib import Path
import tempfile
import os

from analysis.train import (
    load_graph_data_from_csv,
    train_gnn,
    train_rf,
    get_memory_usage_gb
)

@pytest.fixture
def sample_train_csv():
    """Create a temporary CSV file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("smiles,target,feature1,feature2,feature3\n")
        f.write("CCO,1.5,0.1,0.2,0.3\n")
        f.write("CCCO,2.0,0.4,0.5,0.6\n")
        f.write("CCCCO,2.5,0.7,0.8,0.9\n")
        f.write("CCCCCO,3.0,1.0,1.1,1.2\n")
        f.write("CCCCCCO,3.5,1.3,1.4,1.5\n")
        return f.name

@pytest.fixture
def sample_test_csv():
    """Create a temporary CSV file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("smiles,target,feature1,feature2,feature3\n")
        f.write("CCCCCCCO,4.0,1.6,1.7,1.8\n")
        f.write("CCCCCCCCO,4.5,1.9,2.0,2.1\n")
        f.write("CCCCCCCCCO,5.0,2.2,2.3,2.4\n")
        return f.name

def test_load_graph_data_from_csv(sample_train_csv, sample_test_csv):
    """Test loading graph data from CSV files."""
    train_data, test_data = load_graph_data_from_csv(
        Path(sample_train_csv),
        Path(sample_test_csv)
    )
    
    assert 'graphs' in train_data
    assert 'features' in train_data
    assert 'targets' in train_data
    assert 'feature_names' in train_data
    
    assert 'graphs' in test_data
    assert 'features' in test_data
    assert 'targets' in test_data
    assert 'feature_names' in test_data
    
    assert len(train_data['graphs']) == 5
    assert len(test_data['graphs']) == 3
    
    assert train_data['features'].shape == (5, 3)
    assert test_data['features'].shape == (3, 3)
    
    assert len(train_data['targets']) == 5
    assert len(test_data['targets']) == 3
    
    # Clean up
    os.unlink(sample_train_csv)
    os.unlink(sample_test_csv)

def test_get_memory_usage_gb():
    """Test memory usage measurement."""
    memory = get_memory_usage_gb()
    assert isinstance(memory, float)
    assert memory > 0
    assert memory < 100  # Reasonable upper bound

def test_train_rf_basic(sample_train_csv, sample_test_csv):
    """Test basic Random Forest training."""
    train_data, test_data = load_graph_data_from_csv(
        Path(sample_train_csv),
        Path(sample_test_csv)
    )
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "rf_model.pkl"
        metrics = train_rf(train_data, test_data, output_path, n_estimators=5)
        
        assert 'training_duration' in metrics
        assert 'peak_memory_gb' in metrics
        assert 'n_estimators' in metrics
        assert metrics['n_estimators'] == 5
        
        assert output_path.exists()
    
    # Clean up
    os.unlink(sample_train_csv)
    os.unlink(sample_test_csv)

def test_train_gnn_basic(sample_train_csv, sample_test_csv):
    """Test basic GNN training (with small parameters for speed)."""
    train_data, test_data = load_graph_data_from_csv(
        Path(sample_train_csv),
        Path(sample_test_csv)
    )
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "gnn_model.pt"
        metrics = train_gnn(
            train_data,
            test_data,
            output_path,
            patience=2,
            max_epochs=3,
            batch_size=2
        )
        
        assert 'training_duration' in metrics
        assert 'peak_memory_gb' in metrics
        assert 'epochs_trained' in metrics
        assert 'early_stopped' in metrics
        assert metrics['epochs_trained'] <= 3
        
        assert output_path.exists()
    
    # Clean up
    os.unlink(sample_train_csv)
    os.unlink(sample_test_csv)

def test_load_data_missing_file():
    """Test that missing files raise appropriate errors."""
    with pytest.raises(FileNotFoundError):
        load_graph_data_from_csv(
            Path("/nonexistent/train.csv"),
            Path("/nonexistent/test.csv")
        )

def test_load_data_with_nan(sample_train_csv, sample_test_csv):
    """Test handling of NaN values in data."""
    # Create CSV with NaN values
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("smiles,target,feature1,feature2,feature3\n")
        f.write("CCO,1.5,0.1,0.2,0.3\n")
        f.write("CCCO,NaN,0.4,0.5,0.6\n")  # NaN target
        f.write("CCCCO,2.5,NaN,0.8,0.9\n")  # NaN feature
        return f.name
    
    train_path = Path(f.name)
    test_path = Path(sample_test_csv)
    
    # Should handle NaN without crashing
    train_data, test_data = load_graph_data_from_csv(train_path, test_path)
    
    # NaN rows should be removed or handled
    assert len(train_data['targets']) <= 3  # At most 3 valid rows
    
    # Clean up
    os.unlink(f.name)
    os.unlink(sample_train_csv)
    os.unlink(sample_test_csv)