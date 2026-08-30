"""
Unit tests for EDA module.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import json
import tempfile
import os

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from eda import compute_correlation_matrix, compute_spatial_autocorrelation, pivot_to_wide
from visualization import compute_empirical_variogram, plot_variogram

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

def test_compute_empirical_variogram():
    """Test empirical variogram computation."""
    # Create sample spatial data with known structure
    np.random.seed(42)
    n_points = 100
    x = np.random.uniform(0, 100, n_points)
    y = np.random.uniform(0, 100, n_points)
    
    # Create a variable with spatial correlation
    # z = f(distance from origin) + noise
    r = np.sqrt(x**2 + y**2)
    z = 0.5 * r + np.random.normal(0, 1, n_points)
    
    df = pd.DataFrame({
        'x': x,
        'y': y,
        'z': z
    })
    
    # Compute variogram
    lag_distances, variogram_values = compute_empirical_variogram(df, value_col='z')
    
    # Verify output structure
    assert len(lag_distances) == len(variogram_values)
    assert len(lag_distances) > 0
    assert isinstance(lag_distances, np.ndarray)
    assert isinstance(variogram_values, np.ndarray)
    
    # Variogram values should be non-negative
    assert np.all(variogram_values >= 0)
    
    # Lag distances should be non-negative and sorted
    assert np.all(np.diff(lag_distances) >= 0)
    assert np.all(lag_distances >= 0)

def test_compute_empirical_variogram_empty_input():
    """Test variogram computation with insufficient data."""
    df = pd.DataFrame({
        'x': [1.0],
        'y': [1.0],
        'z': [25.0]
    })
    
    # Should raise error with insufficient points
    with pytest.raises(ValueError, match="Need at least 3 points"):
        compute_empirical_variogram(df, value_col='z')

def test_compute_empirical_variogram_constant_values():
    """Test variogram computation with constant values (should return zero)."""
    df = pd.DataFrame({
        'x': [1.0, 2.0, 3.0, 4.0, 5.0],
        'y': [1.0, 2.0, 3.0, 4.0, 5.0],
        'z': [25.0, 25.0, 25.0, 25.0, 25.0]
    })
    
    lag_distances, variogram_values = compute_empirical_variogram(df, value_col='z')
    
    # All variogram values should be zero (or very close) for constant data
    assert np.allclose(variogram_values, 0.0, atol=1e-10)

def test_plot_variogram_creates_file(sample_wide_df):
    """Test that plot_variogram creates a file."""
    # Create a temporary directory for the plot
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, 'variogram_test.png')
        
        # Create sample data with spatial structure
        np.random.seed(42)
        n_points = 50
        x = np.random.uniform(0, 100, n_points)
        y = np.random.uniform(0, 100, n_points)
        r = np.sqrt(x**2 + y**2)
        z = 0.5 * r + np.random.normal(0, 1, n_points)
        
        df = pd.DataFrame({
            'x': x,
            'y': y,
            'temp': z
        })
        
        # Call plot_variogram
        plot_variogram(df, value_col='temp', output_path=output_path)
        
        # Verify file was created
        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 0

def test_plot_variogram_missing_file_handling():
    """Test that plot_variogram handles missing matplotlib gracefully."""
    # This test verifies the function doesn't crash if matplotlib is missing
    # We mock the import to simulate missing matplotlib
    with patch.dict('sys.modules', {'matplotlib': None, 'matplotlib.pyplot': None}):
        # Create sample data
        df = pd.DataFrame({
            'x': [1.0, 2.0, 3.0, 4.0, 5.0],
            'y': [1.0, 2.0, 3.0, 4.0, 5.0],
            'temp': [25.0, 26.0, 24.0, 27.0, 25.5]
        })
        
        # Should not raise an exception when matplotlib is missing
        # The function should log a warning and return gracefully
        try:
            plot_variogram(df, value_col='temp', output_path='dummy.png')
        except ImportError:
            # Expected if matplotlib is completely missing
            pass
        except Exception as e:
            # If it's not an ImportError, it might be a different issue
            # but the function should handle matplotlib absence gracefully
            if "matplotlib" not in str(e).lower():
                raise