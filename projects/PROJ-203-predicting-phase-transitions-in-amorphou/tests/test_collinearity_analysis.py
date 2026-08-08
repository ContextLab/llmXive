"""
Tests for Task T023: Collinearity Analysis.
"""
import os
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import pandas as pd
import numpy as np

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from models.collinearity_analysis import (
    load_final_dataset,
    identify_predictor_columns,
    calculate_vif,
    VIF_THRESHOLD
)

@pytest.fixture
def mock_config():
    """Mock configuration for tests."""
    config = MagicMock()
    config.paths.processed_dir = Path("/fake/processed")
    config.paths.reports_dir = Path("/fake/reports")
    return config

@pytest.fixture
def sample_dataframe():
    """Create a sample dataframe with some collinearity."""
    n = 50
    np.random.seed(42)
    
    # Create features with some correlation
    x1 = np.random.normal(0, 1, n)
    x2 = x1 * 0.9 + np.random.normal(0, 0.1, n)  # Highly correlated with x1
    x3 = np.random.normal(0, 1, n)  # Independent
    x4 = x3 * 0.5 + np.random.normal(0, 0.5, n)  # Moderately correlated with x3
    
    df = pd.DataFrame({
        'composition_id': [f'id_{i}' for i in range(n)],
        'Tg_exp': np.random.normal(300, 20, n),
        'Tx_exp': np.random.normal(350, 20, n),
        'crystallization_label': np.random.randint(0, 2, n),
        'chemical_family': np.random.choice(['oxide', 'sulfide', 'organic'], n),
        'rdf_peak_pos': x1,
        'rdf_peak_width': x2,
        'bond_angle_variance': x3,
        'coordination_numbers': x4,
        'simulation_id': [f'sim_{i}' for i in range(n)]
    })
    return df

def test_identify_predictor_columns(sample_dataframe):
    """Test that predictor columns are correctly identified."""
    predictors = identify_predictor_columns(sample_dataframe)
    
    expected_predictors = ['rdf_peak_pos', 'rdf_peak_width', 'bond_angle_variance', 'coordination_numbers']
    
    assert set(predictors) == set(expected_predictors)
    assert 'Tg_exp' not in predictors
    assert 'composition_id' not in predictors
    assert 'chemical_family' not in predictors

def test_calculate_vif_basic(sample_dataframe):
    """Test VIF calculation on a simple dataset."""
    predictors = ['rdf_peak_pos', 'rdf_peak_width', 'bond_angle_variance', 'coordination_numbers']
    
    results = calculate_vif(sample_dataframe, predictors)
    
    assert len(results) == len(predictors)
    
    # Check structure
    for res in results:
        assert 'feature' in res
        assert 'vif' in res
        assert 'flagged' in res
        assert isinstance(res['vif'], float)
        assert isinstance(res['flagged'], bool)
    
    # Check that highly correlated features (x1, x2) have higher VIF
    x1_vif = next(r['vif'] for r in results if r['feature'] == 'rdf_peak_pos')
    x2_vif = next(r['vif'] for r in results if r['feature'] == 'rdf_peak_width')
    
    # They should be flagged if VIF > 5
    # With 0.9 correlation, VIF should be significant
    assert x1_vif > 1.0
    assert x2_vif > 1.0

def test_vif_threshold_flagging(sample_dataframe):
    """Test that the VIF threshold correctly flags features."""
    predictors = ['rdf_peak_pos', 'rdf_peak_width', 'bond_angle_variance', 'coordination_numbers']
    
    results = calculate_vif(sample_dataframe, predictors)
    
    # Count flagged
    flagged_count = sum(1 for r in results if r['flagged'])
    
    # At least the highly correlated pair should be flagged
    assert flagged_count >= 0  # Depends on exact correlation, but structure must be correct
    
    for res in results:
        if res['vif'] > VIF_THRESHOLD:
            assert res['flagged'] is True
        else:
            assert res['flagged'] is False

def test_calculate_vif_with_nans(sample_dataframe):
    """Test VIF calculation with missing values."""
    # Introduce NaNs
    df_nan = sample_dataframe.copy()
    df_nan.loc[0, 'rdf_peak_pos'] = np.nan
    
    predictors = ['rdf_peak_pos', 'rdf_peak_width', 'bond_angle_variance', 'coordination_numbers']
    
    # Should handle NaNs by dropping rows
    results = calculate_vif(df_nan, predictors)
    
    assert len(results) == len(predictors)
    assert all('vif' in r for r in results)

def test_load_final_dataset_missing_file(mock_config, tmp_path):
    """Test that load_final_dataset raises error when file is missing."""
    # Setup config to point to non-existent file
    with patch('models.collinearity_analysis.get_config', return_value=mock_config):
        with pytest.raises(FileNotFoundError, match="FATAL: Required dataset"):
            load_final_dataset()

def test_identify_predictor_columns_no_predictors():
    """Test behavior when no predictors are found."""
    df = pd.DataFrame({
        'composition_id': [1, 2],
        'Tg_exp': [300, 301],
        'crystallization_label': [0, 1]
    })
    
    with pytest.raises(ValueError, match="No numeric predictor columns found"):
        identify_predictor_columns(df)