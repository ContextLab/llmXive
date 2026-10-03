"""
Unit tests for the sensitivity_sweep function in code/analysis.py.
"""
import os
import sys
import numpy as np
import pandas as pd
import torch
import pytest
from pathlib import Path
from unittest.mock import Mock, patch

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from analysis import sensitivity_sweep
from torch_geometric.data import Data

def create_mock_graph(target_val: float) -> Data:
    """Create a simple mock graph for testing."""
    x = torch.tensor([[1.0], [2.0]], dtype=torch.float)
    edge_index = torch.tensor([[0, 1], [1, 0]], dtype=torch.long)
    y = torch.tensor([target_val], dtype=torch.float)
    return Data(x=x, edge_index=edge_index, y=y)

def create_mock_model() -> Mock:
    """Create a mock model that returns deterministic predictions."""
    model = Mock()
    model.eval = Mock(return_value=None)
    model.device = torch.device('cpu')
    
    # Mock the forward pass to return specific values
    def mock_forward(graph):
        # Return a value that depends on the target for simplicity in testing
        # In reality, this would be the model's prediction
        return torch.tensor([0.5], dtype=torch.float)
    
    model.__call__ = mock_forward
    return model

def test_sensitivity_sweep_basic():
    """Test basic functionality of sensitivity_sweep."""
    model = create_mock_model()
    data = [create_mock_graph(1.0), create_mock_graph(2.0), create_mock_graph(3.0)]
    widths = [0.1, 0.5, 1.0]
    
    result_df = sensitivity_sweep(model, data, widths)
    
    assert isinstance(result_df, pd.DataFrame)
    assert list(result_df.columns) == ['width', 'mae', 'ci']
    assert len(result_df) == len(widths)
    
    # Check that 'width' and 'ci' match
    assert all(result_df['width'] == result_df['ci'])
    
    # Check that MAE is a single constant value (global MAE in this impl)
    assert result_df['mae'].nunique() == 1

def test_sensitivity_sweep_empty_data():
    """Test behavior with empty data list."""
    model = create_mock_model()
    data = []
    widths = [0.1]
    
    with pytest.raises(ValueError, match="No valid predictions generated"):
        sensitivity_sweep(model, data, widths)

def test_sensitivity_sweep_invalid_widths():
    """Test behavior with empty widths list."""
    model = create_mock_model()
    data = [create_mock_graph(1.0)]
    widths = []
    
    with pytest.raises(ValueError, match="No widths provided"):
        sensitivity_sweep(model, data, widths)

def test_sensitivity_sweep_numeric_types():
    """Test that output columns have correct numeric types."""
    model = create_mock_model()
    data = [create_mock_graph(1.0)]
    widths = [0.1, 0.2]
    
    result_df = sensitivity_sweep(model, data, widths)
    
    assert np.isnumeric(result_df['width'].values)
    assert np.isnumeric(result_df['mae'].values)
    assert np.isnumeric(result_df['ci'].values)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])