"""
Unit tests for the geometry-only baseline training script.
"""
import os
import sys
import tempfile
import shutil
import pandas as pd
import numpy as np
import torch
import pytest

# Add code to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from train_baseline import (
    GeometryOnlyDataset, 
    GeometryBaselineModel, 
    collate_fn, 
    set_seed,
    train_epoch,
    evaluate
)

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory with mock data."""
    temp_dir = tempfile.mkdtemp()
    data_path = os.path.join(temp_dir, "train.parquet")
    
    # Create mock data
    n_samples = 100
    bounds = np.random.rand(n_samples, 6).astype(np.float32)
    labels = np.random.randint(0, 2, n_samples).astype(np.int64)
    
    df = pd.DataFrame({
        'initial_object_bounds': list(bounds),
        'stability_label': labels,
        'geometry_id': [f"geo_{i}" for i in range(n_samples)]
    })
    df.to_parquet(data_path)
    
    yield data_path
    
    # Cleanup
    shutil.rmtree(temp_dir)

def test_geometry_dataset_loads(temp_data_dir):
    """Test that the dataset loads correctly."""
    dataset = GeometryOnlyDataset(temp_data_dir)
    assert len(dataset) == 100
    x, y = dataset[0]
    assert x.shape == (6,)
    assert y.shape == (1,)
    assert x.dtype == torch.float32
    assert y.dtype == torch.float32

def test_model_forward():
    """Test model forward pass."""
    model = GeometryBaselineModel(input_dim=6, hidden_dim=32)
    x = torch.randn(4, 6)
    out = model(x)
    assert out.shape == (4, 1)

def test_collate_fn():
    """Test collate function."""
    dataset = type('MockDataset', (), {
        '__len__': lambda self: 2,
        '__getitem__': lambda self, i: (torch.tensor([1.0]*6), torch.tensor([0.0]))
    })()
    
    batch = [(torch.tensor([1.0]*6), torch.tensor([0.0])) for _ in range(2)]
    xs, ys = collate_fn(batch)
    assert xs.shape == (2, 6)
    assert ys.shape == (2,)

def test_train_epoch_runs():
    """Test that training epoch runs without error."""
    model = GeometryBaselineModel()
    x = torch.randn(4, 6)
    y = torch.randn(4, 1)
    loader = torch.utils.data.DataLoader(
        torch.utils.data.TensorDataset(x, y), 
        batch_size=2
    )
    optimizer = torch.optim.Adam(model.parameters())
    criterion = torch.nn.BCEWithLogitsLoss()
    
    loss, acc = train_epoch(model, loader, optimizer, criterion, torch.device('cpu'))
    assert isinstance(loss, float)
    assert 0.0 <= acc <= 1.0

def test_evaluate_runs():
    """Test that evaluation runs without error."""
    model = GeometryBaselineModel()
    x = torch.randn(4, 6)
    y = torch.randn(4, 1)
    loader = torch.utils.data.DataLoader(
        torch.utils.data.TensorDataset(x, y), 
        batch_size=2
    )
    criterion = torch.nn.BCEWithLogitsLoss()
    
    loss, acc = evaluate(model, loader, criterion, torch.device('cpu'))
    assert isinstance(loss, float)
    assert 0.0 <= acc <= 1.0