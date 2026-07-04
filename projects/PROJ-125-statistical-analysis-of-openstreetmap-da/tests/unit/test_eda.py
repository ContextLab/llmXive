"""
Unit tests for EDA module.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from eda import compute_correlation_matrix, compute_spatial_autocorrelation, pivot_to_wide

@pytest.fixture
def sample_long_df():
    """Create sample long-format DataFrame."""
    return pd.DataFrame({
        'x': [1, 1, 2, 2, 3, 3],
        'y': [1, 2, 1, 2, 1, 2],
        'variable': ['temp', 'temp', 'temp', 'temp', 'temp', 'temp',
                    'building', 'building', 'building', 'building', 'building', 'building'],
        'value': [25.0, 26.0, 24.0, 27.0, 25.5, 26.5,
                 0.3, 0.4, 0.35, 0.45, 0.32, 0.42]
    })

@pytest.fixture
def sample_wide_df():
    """Create sample wide-format DataFrame."""
    return pd.DataFrame({
        'x': [1, 1, 2, 2, 3, 3],
        'y': [1, 2, 1, 2, 1, 2],
        'temp': [25.0, 26.0, 24.0, 27.0, 25.5, 26.5],
        'building': [0.3, 0.4, 0.35, 0.45, 0.32, 0.42],
        'roads': [0.1, 0.2, 0.15, 0.25, 0.12, 0.22]
    })

def test_pivot_to_wide(sample_long_df):
    """Test pivoting from long to wide format."""
    # Create a proper long format with multiple variables
    long_df = pd.DataFrame({
        'x': [1, 1, 2, 2],
        'y': [1, 2, 1, 2],
        'variable': ['temp', 'temp', 'building', 'building'],
        'value': [25.0, 26.0, 0.3, 0.4]
    })
    
    wide_df = pivot_to_wide(long_df)
    
    assert 'temp' in wide_df.columns
    assert 'building' in wide_df.columns
    assert 'x' in wide_df.columns
    assert 'y' in wide_df.columns
    assert len(wide_df) == 2  # 2 unique (x, y) pairs

def test_compute_correlation_matrix_pearson(sample_wide_df):
    """Test Pearson correlation computation."""
    corr, pval = compute_correlation_matrix(sample_wide_df, method='pearson')
    
    assert isinstance(corr, pd.DataFrame)
    assert isinstance(pval, pd.DataFrame)
    assert corr.shape[0] == corr.shape[1]
    assert 'temp' in corr.columns
    assert 'building' in corr.columns
    
    # Diagonal should be 1.0
    for col in corr.columns:
        assert corr.loc[col, col] == 1.0

def test_compute_correlation_matrix_spearman(sample_wide_df):
    """Test Spearman correlation computation."""
    corr, pval = compute_correlation_matrix(sample_wide_df, method='spearman')
    
    assert isinstance(corr, pd.DataFrame)
    assert isinstance(pval, pd.DataFrame)
    assert corr.shape[0] == corr.shape[1]

def test_compute_correlation_matrix_insufficient_data():
    """Test error handling for insufficient data."""
    df = pd.DataFrame({'x': [1, 2], 'y': [1, 2], 'temp': [25.0, 26.0]})
    
    with pytest.raises(ValueError, match="Need at least 2 numeric variables"):
        compute_correlation_matrix(df)

def test_compute_spatial_autocorrelation(sample_wide_df):
    """Test Moran's I computation."""
    with patch('eda.get_city_crs') as mock_crs:
        mock_crs.return_value = 'EPSG:3857'
        
        results = compute_spatial_autocorrelation(sample_wide_df, temperature_var='temp')
        
        assert 'moran_i' in results
        assert 'expected_i' in results
        assert 'p_value' in results
        assert 'n' in results
        assert isinstance(results['moran_i'], float)
        assert isinstance(results['p_value'], float)

def test_compute_spatial_autocorrelation_missing_var(sample_wide_df):
    """Test error handling for missing temperature variable."""
    with patch('eda.get_city_crs') as mock_crs:
        mock_crs.return_value = 'EPSG:3857'
        
        with pytest.raises(ValueError, match="Temperature variable 'nonexistent' not found"):
            compute_spatial_autocorrelation(sample_wide_df, temperature_var='nonexistent')
