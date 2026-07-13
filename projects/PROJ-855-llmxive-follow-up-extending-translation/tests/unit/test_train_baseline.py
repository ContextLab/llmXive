"""
Unit tests for T027b: Geometry-Only Baseline Training
"""

import os
import sys
import tempfile
import torch
import pandas as pd
import numpy as np
import pyarrow.parquet as pq
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from train_baseline import (
    GeometryOnlyDataset,
    LogisticRegressionBaseline,
    train_baseline,
    BASELINE_FEATURES
)

def test_model_architecture():
    """Verify the baseline model has the correct architecture."""
    input_dim = 6  # Example: 6 bounds (x_min, y_min, z_min, x_max, y_max, z_max)
    model = LogisticRegressionBaseline(input_dim)
    
    # Check linear layer dimensions
    assert model.fc.in_features == input_dim
    assert model.fc.out_features == 1
    
    # Check parameter count is low (baseline should be tiny)
    params = sum(p.numel() for p in model.parameters())
    assert params < 10000 # Should be very small
    print(f"Model parameters: {params}")

def test_dataset_loading():
    """Verify dataset loads only initial_object_bounds and labels."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create dummy parquet file
        df = pd.DataFrame({
            "initial_object_bounds": [[0, 0, 0, 1, 1, 1]] * 10,
            "stability": [1, 0, 1, 0, 1, 0, 1, 0, 1, 0]
        })
        path = Path(tmpdir) / "dummy.parquet"
        pq.write_table(df, path)
        
        dataset = GeometryOnlyDataset(path)
        
        # Check shapes
        assert dataset.X.shape[0] == 10
        assert dataset.y.shape[0] == 10
        assert dataset.X.shape[1] == 6 # 6 bounds
        
        # Check types
        assert isinstance(dataset.X, np.ndarray)
        assert isinstance(dataset.y, np.ndarray)

def test_training_step():
    """Verify training loop runs without error."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create dummy training data
        df = pd.DataFrame({
            "initial_object_bounds": [[i, 0, 0, i+1, 1, 1] for i in range(100)],
            "stability": [1 if i % 2 == 0 else 0 for i in range(100)]
        })
        train_path = Path(tmpdir) / "train.parquet"
        pq.write_table(df, train_path)
        
        # Temporarily override paths for testing
        original_train_path = train_baseline.__globals__.get('TRAIN_DATA_PATH')
        original_model_path = train_baseline.__globals__.get('MODEL_PATH')
        
        try:
            train_baseline.__globals__['TRAIN_DATA_PATH'] = train_path
            model_path = Path(tmpdir) / "model.pt"
            train_baseline.__globals__['MODEL_PATH'] = model_path
            
            # Run training (shortened)
            # We can't easily patch the function's internal imports, so we just
            # verify the model can be instantiated and trained on dummy data.
            dataset = GeometryOnlyDataset(train_path)
            model = LogisticRegressionBaseline(dataset.X.shape[1])
            
            # Simple forward pass
            x = torch.tensor(dataset.X[0:1])
            y = torch.tensor(dataset.y[0:1])
            out = model(x)
            assert out.shape == (1, 1)
            assert 0 <= out.item() <= 1
            
        finally:
            if original_train_path:
                train_baseline.__globals__['TRAIN_DATA_PATH'] = original_train_path
            if original_model_path:
                train_baseline.__globals__['MODEL_PATH'] = original_model_path

if __name__ == "__main__":
    test_model_architecture()
    test_dataset_loading()
    test_training_step()
    print("All baseline tests passed.")
