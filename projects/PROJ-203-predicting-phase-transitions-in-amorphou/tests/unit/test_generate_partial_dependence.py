"""
Unit tests for T026: Partial Dependence Plot Generation.
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
from pathlib import Path
import json
import tempfile
import os

# Mock imports that might fail in test environment without full data
import sys
from io import StringIO

@pytest.fixture
def mock_config():
    """Mock config object."""
    config = MagicMock()
    config.paths.reports_dir = "/mock/reports"
    config.paths.figures_dir = "/mock/figures"
    config.data.processed_dir = "/mock/data/processed"
    return config

@pytest.fixture
def mock_dataset():
    """Create a mock dataset."""
    data = {
        'composition_id': [f'ID_{i}' for i in range(10)],
        'Tg_K': [400 + i * 10 for i in range(10)],
        'Tx_K': [500 + i * 10 for i in range(10)],
        'chemical_family': ['Oxide'] * 4 + ['Sulfide'] * 3 + ['Organic'] * 3,
        'rdf_peak_pos': np.random.rand(10),
        'rdf_peak_width': np.random.rand(10),
        'bond_angle_variance': np.random.rand(10),
        'coordination_numbers': np.random.rand(10),
        'crystallization_label': [0, 1] * 5
    }
    return pd.DataFrame(data)

@pytest.fixture
def mock_rankings():
    """Mock SHAP rankings."""
    return {
        'Oxide': ['rdf_peak_pos', 'bond_angle_variance', 'coordination_numbers'],
        'Sulfide': ['rdf_peak_pos', 'rdf_peak_width', 'coordination_numbers'],
        'Organic': ['bond_angle_variance', 'rdf_peak_pos', 'coordination_numbers']
    }

def test_get_top_predictors(mock_rankings):
    """Test extraction of top N predictors."""
    from models.generate_partial_dependence import get_top_predictors
    
    result = get_top_predictors(mock_rankings, n_top=2)
    
    assert 'Oxide' in result
    assert len(result['Oxide']) == 2
    assert result['Oxide'][0] == 'rdf_peak_pos'
    assert result['Oxide'][1] == 'bond_angle_variance'

@patch('models.generate_partial_dependence.get_config')
@patch('models.generate_partial_dependence.load_models')
@patch('models.generate_partial_dependence.load_final_dataset')
@patch('models.generate_partial_dependence.load_shap_rankings')
def test_main_execution(mock_load_rankings, mock_load_dataset, mock_load_models, mock_get_config, mock_dataset, mock_rankings):
    """Test the main execution flow."""
    from models.generate_partial_dependence import main
    
    # Setup mocks
    mock_get_config.return_value.paths.reports_dir = "/tmp"
    mock_get_config.return_value.paths.figures_dir = "/tmp"
    mock_get_config.return_value.data.processed_dir = "/tmp"
    mock_load_models.return_value = {"tg_regressor": MagicMock()}
    mock_load_dataset.return_value = mock_dataset
    mock_load_rankings.return_value = mock_rankings
    
    # Mock matplotlib to avoid display issues
    with patch('matplotlib.pyplot.savefig'):
        with patch('matplotlib.pyplot.close'):
            with patch('pathlib.Path.mkdir'):
                with patch('builtins.open', mock_open_with_temp_dir()):
                    result = main()
    
    assert result == 0

def mock_open_with_temp_dir():
    """Helper to mock file opening in a temp directory."""
    return patch('builtins.open', new_callable=unittest.mock.mock_open)

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
