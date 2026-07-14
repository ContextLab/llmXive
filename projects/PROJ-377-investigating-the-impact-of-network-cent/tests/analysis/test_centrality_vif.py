import pytest
import pandas as pd
import numpy as np
import os
import tempfile
from pathlib import Path

# Mock the utils.config to avoid missing config errors in tests
import sys
from unittest.mock import patch, MagicMock

@pytest.fixture
def mock_config():
    mock = MagicMock()
    mock.get_vif_threshold.return_value = 5.0
    mock.get_fixed_region_indices.return_value = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    return mock

@pytest.fixture
def sample_metrics_df():
    # Create a dataframe simulating T020 output
    data = {
        'subject_id': ['sub-01', 'sub-02', 'sub-03', 'sub-04', 'sub-05'],
        'age': [20, 21, 22, 23, 24],
        'sex': ['M', 'F', 'M', 'F', 'M'],
        'degree': [
            '[0.1, 0.2, 0.1, 0.2, 0.1, 0.2, 0.1, 0.2, 0.1, 0.2, 0.1, 0.2]',
            '[0.1, 0.2, 0.1, 0.2, 0.1, 0.2, 0.1, 0.2, 0.1, 0.2, 0.1, 0.2]',
            '[0.1, 0.2, 0.1, 0.2, 0.1, 0.2, 0.1, 0.2, 0.1, 0.2, 0.1, 0.2]',
            '[0.1, 0.2, 0.1, 0.2, 0.1, 0.2, 0.1, 0.2, 0.1, 0.2, 0.1, 0.2]',
            '[0.1, 0.2, 0.1, 0.2, 0.1, 0.2, 0.1, 0.2, 0.1, 0.2, 0.1, 0.2]'
        ],
        'betweenness': [
            '[0.01, 0.02, 0.01, 0.02, 0.01, 0.02, 0.01, 0.02, 0.01, 0.02, 0.01, 0.02]',
            '[0.01, 0.02, 0.01, 0.02, 0.01, 0.02, 0.01, 0.02, 0.01, 0.02, 0.01, 0.02]',
            '[0.01, 0.02, 0.01, 0.02, 0.01, 0.02, 0.01, 0.02, 0.01, 0.02, 0.01, 0.02]',
            '[0.01, 0.02, 0.01, 0.02, 0.01, 0.02, 0.01, 0.02, 0.01, 0.02, 0.01, 0.02]',
            '[0.01, 0.02, 0.01, 0.02, 0.01, 0.02, 0.01, 0.02, 0.01, 0.02, 0.01, 0.02]'
        ],
        'eigenvector': [
            '[0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5]',
            '[0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5]',
            '[0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5]',
            '[0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5]',
            '[0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5]'
        ]
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_fd_df():
    return pd.DataFrame({
        'subject_id': ['sub-01', 'sub-02', 'sub-03', 'sub-04', 'sub-05'],
        'mean_fd': [0.1, 0.2, 0.15, 0.25, 0.12]
    })

def test_vif_calculation_low_vif(sample_metrics_df, sample_fd_df, mock_config):
    """Test that low VIF results in Global_Centrality being used."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        metrics_path = tmpdir / "metrics.csv"
        fd_path = tmpdir / "fd.csv"
        output_path = tmpdir / "predictors.csv"
        
        sample_metrics_df.to_csv(metrics_path, index=False)
        sample_fd_df.to_csv(fd_path, index=False)
        
        # Patch config
        with patch('analysis.centrality.get_vif_threshold', return_value=10.0): # High threshold
            with patch('analysis.centrality.get_fixed_region_indices', return_value=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9]):
                from analysis.centrality import run_vif_and_select_predictors
                result, use_pca = run_vif_and_select_predictors(metrics_path, fd_path, output_path)
                
                assert not use_pca
                assert 'Global_Centrality' in result.columns
                assert 'PCA_Component_1' not in result.columns or result['PCA_Component_1'].isna().all()

def test_vif_calculation_high_vif(sample_metrics_df, sample_fd_df, mock_config):
    """Test that high VIF results in PCA being used."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        metrics_path = tmpdir / "metrics.csv"
        fd_path = tmpdir / "fd.csv"
        output_path = tmpdir / "predictors.csv"
        
        # Create data with perfect correlation to force high VIF
        # Make degree, betweenness, eigenvector identical
        identical_val = '[0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1]'
        data = {
            'subject_id': ['sub-01', 'sub-02', 'sub-03', 'sub-04', 'sub-05'],
            'age': [20, 21, 22, 23, 24],
            'sex': ['M', 'F', 'M', 'F', 'M'],
            'degree': [identical_val] * 5,
            'betweenness': [identical_val] * 5,
            'eigenvector': [identical_val] * 5
        }
        high_vif_df = pd.DataFrame(data)
        high_vif_df.to_csv(metrics_path, index=False)
        sample_fd_df.to_csv(fd_path, index=False)
        
        # Patch config with low threshold
        with patch('analysis.centrality.get_vif_threshold', return_value=1.0):
            with patch('analysis.centrality.get_fixed_region_indices', return_value=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9]):
                from analysis.centrality import run_vif_and_select_predictors
                result, use_pca = run_vif_and_select_predictors(metrics_path, fd_path, output_path)
                
                assert use_pca
                assert 'PCA_Component_1' in result.columns
                assert 'Global_Centrality' not in result.columns or result['Global_Centrality'].isna().all()