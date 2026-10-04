"""
Unit tests for T023c: Result Aggregation Logic.
"""
import pytest
import json
import torch
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.models.aggregate_ensemble import (
    load_models_from_checkpoints,
    aggregate_predictions,
    save_results
)

@pytest.fixture
def mock_models():
    """Create mock SchNet models."""
    models = []
    for _ in range(5):
        model = MagicMock()
        model.eval.return_value = None
        models.append(model)
    return models

@pytest.fixture
def mock_graphs_df():
    """Create a mock graphs DataFrame."""
    import pandas as pd
    data = {
        'sample_id': [f'sample_{i}' for i in range(10)],
        'x': [np.random.rand(10, 5).tolist() for _ in range(10)], # 10 nodes, 5 features
        'edge_index': [[[0, 1], [1, 2]] for _ in range(10)],
        'y': [1.0 + i * 0.1 for i in range(10)]
    }
    # Create edge_index as 2D tensor
    data['edge_index'] = [np.array([[0, 1, 1, 2], [1, 0, 2, 1]]) for _ in range(10)]
    return pd.DataFrame(data)

@pytest.fixture
def mock_splits():
    """Create mock splits data."""
    return {
        'train': [0, 1, 2, 3, 4],
        'val': [5, 6],
        'test': [7, 8, 9]
    }

@patch('src.models.aggregate_ensemble.load_checkpoint')
@patch('pathlib.Path.exists', return_value=True)
def test_load_models_from_checkpoints(mock_exists, mock_load, mock_models):
    """Test loading models from checkpoints."""
    mock_load.return_value = MagicMock()
    checkpoint_dir = Path("/fake/dir")
    
    models = load_models_from_checkpoints(checkpoint_dir, num_models=5)
    
    assert len(models) == 5
    assert mock_load.call_count == 5

@patch('src.models.aggregate_ensemble.get_logger')
@patch('src.models.aggregate_ensemble.json.load')
@patch('src.models.aggregate_ensemble.pd.read_parquet')
def test_aggregate_predictions(
    mock_read_parquet, mock_json_load, mock_logger, mock_models, mock_graphs_df, mock_splits
):
    """Test aggregation of predictions."""
    # Setup mocks
    mock_read_parquet.return_value = mock_graphs_df
    mock_json_load.return_value = mock_splits
    
    # Mock model prediction
    for model in mock_models:
        model.return_value = torch.tensor([1.0]) # Return a scalar prediction
    
    # Run aggregation
    result_df, variance_stats = aggregate_predictions(mock_models, mock_graphs_df)
    
    assert 'ensemble_mean' in result_df.columns
    assert 'ensemble_variance' in result_df.columns
    assert len(result_df) == 3 # 3 test samples
    assert 'mean_variance' in variance_stats
    assert 'num_samples' in variance_stats
    assert variance_stats['num_samples'] == 3

def test_save_results(tmp_path):
    """Test saving results to disk."""
    import pandas as pd
    
    df = pd.DataFrame({
        'sample_id': ['a', 'b'],
        'ensemble_mean': [1.0, 2.0],
        'ensemble_variance': [0.1, 0.2]
    })
    stats = {'mean_variance': 0.15, 'num_samples': 2}
    
    save_results(df, stats, tmp_path)
    
    assert (tmp_path / "ensemble_variance.json").exists()
    assert (tmp_path / "ensemble_predictions.parquet").exists()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])