"""
Unit tests for the climate data imputation module.

Tests for T007 and T020 integration.
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

from src.data.impute import (
    load_climate_data,
    interpolate_spatial,
    save_imputed_data,
    run_imputation_pipeline
)

@pytest.fixture
def sample_climate_data():
    """Create sample climate data with some missing values."""
    np.random.seed(42)
    n_points = 100
    
    data = {
        'lat': np.random.uniform(30, 50, n_points),
        'lon': np.random.uniform(-120, -70, n_points),
        'temp': np.random.normal(15, 5, n_points),
        'week': np.random.randint(1, 53, n_points),
        'precip': np.random.exponential(2, n_points)
    }
    
    df = pd.DataFrame(data)
    
    # Introduce some missing values
    missing_indices = np.random.choice(n_points, size=10, replace=False)
    df.loc[missing_indices, 'temp'] = np.nan
    
    return df

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test outputs."""
    tmpdir = tempfile.mkdtemp()
    yield tmpdir
    shutil.rmtree(tmpdir)

def test_load_climate_data(sample_climate_data, temp_dir):
    """Test loading climate data from parquet file."""
    input_path = Path(temp_dir) / "test_climate.parquet"
    sample_climate_data.to_parquet(input_path)
    
    loaded_df = load_climate_data(str(input_path))
    
    assert loaded_df.equals(sample_climate_data)
    assert list(loaded_df.columns) == ['lat', 'lon', 'temp', 'week', 'precip']

def test_load_climate_data_missing_file():
    """Test that loading non-existent file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_climate_data("/nonexistent/path/climate.parquet")

def test_load_climate_data_missing_columns(temp_dir):
    """Test that missing required columns raise ValueError."""
    input_path = Path(temp_dir) / "bad_climate.parquet"
    bad_df = pd.DataFrame({'lat': [1, 2], 'lon': [3, 4]})  # Missing temp, precip, week
    bad_df.to_parquet(input_path)
    
    with pytest.raises(ValueError):
        load_climate_data(str(input_path))

def test_interpolate_spatial_no_missing(sample_climate_data, temp_dir):
    """Test interpolation when no values are missing."""
    # Create data without missing values
    clean_data = sample_climate_data.copy()
    clean_data['temp'] = clean_data['temp'].fillna(0)
    clean_data['precip'] = clean_data['precip'].fillna(0)
    
    result = interpolate_spatial(clean_data)
    
    assert 'imputed' in result.columns
    assert result['imputed'].sum() == 0
    assert not result['imputed'].any()

def test_interpolate_spatial_with_missing(sample_climate_data, temp_dir):
    """Test interpolation with missing values."""
    result = interpolate_spatial(sample_climate_data)
    
    assert 'imputed' in result.columns
    assert result['imputed'].sum() > 0
    
    # Check that imputed rows have values (or NaN if interpolation failed)
    imputed_rows = result[result['imputed']]
    assert len(imputed_rows) > 0

def test_interpolate_spatial_all_missing(temp_dir):
    """Test interpolation when all values are missing."""
    data = pd.DataFrame({
        'lat': [30, 40, 50],
        'lon': [-120, -100, -80],
        'temp': [np.nan, np.nan, np.nan],
        'week': [1, 2, 3],
        'precip': [np.nan, np.nan, np.nan]
    })
    
    result = interpolate_spatial(data)
    
    assert result['imputed'].all()
    # All values should remain NaN as there's no known data to interpolate from
    assert result['temp'].isna().all()
    assert result['precip'].isna().all()

def test_save_imputed_data(sample_climate_data, temp_dir):
    """Test saving imputed data to parquet."""
    imputed_df = interpolate_spatial(sample_climate_data)
    output_path = Path(temp_dir) / "imputed_climate.parquet"
    
    saved_path = save_imputed_data(imputed_df, str(output_path))
    
    assert Path(saved_path).exists()
    assert saved_path == str(output_path)
    
    # Verify saved data
    saved_df = pd.read_parquet(saved_path)
    assert 'imputed' in saved_df.columns

def test_run_imputation_pipeline(sample_climate_data, temp_dir):
    """Test the full imputation pipeline."""
    input_path = Path(temp_dir) / "input_climate.parquet"
    output_path = Path(temp_dir) / "output_climate.parquet"
    
    sample_climate_data.to_parquet(input_path)
    
    result = run_imputation_pipeline(
        input_path=str(input_path),
        output_path=str(output_path),
        radius_deg=1.0
    )
    
    assert result['success']
    assert Path(result['output_file']).exists()
    assert result['imputed_count'] > 0
    assert result['total_rows'] == len(sample_climate_data)
    assert 'metadata' in result

def test_empty_dataframe():
    """Test handling of empty DataFrame."""
    empty_df = pd.DataFrame(columns=['lat', 'lon', 'temp', 'week', 'precip'])
    
    # Should not crash, just return empty with imputed flag
    result = interpolate_spatial(empty_df)
    assert len(result) == 0
    assert 'imputed' in result.columns

def test_single_point_no_neighbors():
    """Test interpolation with only one data point."""
    data = pd.DataFrame({
        'lat': [40.0],
        'lon': [-100.0],
        'temp': [np.nan],
        'week': [1],
        'precip': [np.nan]
    })
    
    result = interpolate_spatial(data)
    assert result['imputed'].all()
    # Should remain NaN as there are no neighbors
    assert np.isnan(result['temp'].iloc[0])