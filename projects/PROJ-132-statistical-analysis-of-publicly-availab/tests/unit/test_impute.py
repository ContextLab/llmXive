"""
Unit tests for the impute module.
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock

# Add the code directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from src.data.impute import (
    load_climate_data,
    identify_missing_values,
    interpolate_spatial,
    save_imputed_data,
    run_imputation_pipeline
)


@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    tmpdir = tempfile.mkdtemp()
    yield Path(tmpdir)
    shutil.rmtree(tmpdir)


@pytest.fixture
def sample_climate_data():
    """Create sample climate data with some missing values."""
    data = {
        'lat': [40.0, 40.5, 41.0, 40.0, 40.5, 41.0],
        'lon': [-75.0, -75.0, -75.0, -74.0, -74.0, -74.0],
        'temp': [15.0, 16.0, np.nan, 14.0, np.nan, 13.0],
        'week': [1, 1, 1, 2, 2, 2],
        'precip': [10.0, 12.0, 11.0, np.nan, 13.0, 14.0]
    }
    return pd.DataFrame(data)


def test_load_climate_data(temp_data_dir, sample_climate_data):
    """Test loading climate data from parquet."""
    input_path = temp_data_dir / 'test_climate.parquet'
    sample_climate_data.to_parquet(input_path)
    
    df = load_climate_data(str(input_path))
    
    assert len(df) == 6
    assert set(df.columns) == {'lat', 'lon', 'temp', 'week', 'precip'}
    assert df['temp'].isna().sum() == 2


def test_load_climate_data_missing_file(temp_data_dir):
    """Test loading from a non-existent file."""
    with pytest.raises(FileNotFoundError):
        load_climate_data(str(temp_data_dir / 'nonexistent.parquet'))


def test_load_climate_data_missing_columns(temp_data_dir):
    """Test loading data with missing required columns."""
    df = pd.DataFrame({'lat': [1.0], 'lon': [1.0]})
    input_path = temp_data_dir / 'incomplete.parquet'
    df.to_parquet(input_path)
    
    with pytest.raises(ValueError, match="Missing required columns"):
        load_climate_data(str(input_path))


def test_identify_missing_values(sample_climate_data):
    """Test identifying missing values."""
    df_flagged, missing_indices = identify_missing_values(sample_climate_data)
    
    assert len(missing_indices) == 2
    # Check that the flagged DataFrame has the same shape
    assert len(df_flagged) == len(sample_climate_data)


def test_interpolate_spatial_no_missing(temp_data_dir):
    """Test interpolation when there are no missing values."""
    data = {
        'lat': [40.0, 40.5, 41.0],
        'lon': [-75.0, -75.0, -75.0],
        'temp': [15.0, 16.0, 17.0],
        'week': [1, 1, 1],
        'precip': [10.0, 12.0, 11.0]
    }
    df = pd.DataFrame(data)
    
    result = interpolate_spatial(df, ['temp', 'precip'])
    
    # Should be unchanged
    pd.testing.assert_frame_equal(result, df)


def test_interpolate_spatial_with_missing(sample_climate_data):
    """Test interpolation with missing values."""
    # Ensure we have missing values
    assert sample_climate_data['temp'].isna().any()
    
    result = interpolate_spatial(sample_climate_data, ['temp', 'precip'])
    
    # No NaNs should remain in temp or precip
    assert not result['temp'].isna().any()
    assert not result['precip'].isna().any()
    
    # Non-missing values should be preserved
    original_non_missing = sample_climate_data.loc[~sample_climate_data['temp'].isna(), 'temp']
    result_non_missing = result.loc[~sample_climate_data['temp'].isna(), 'temp']
    pd.testing.assert_series_equal(result_non_missing, original_non_missing)


def test_run_imputation_pipeline(temp_data_dir, sample_climate_data):
    """Test the full imputation pipeline."""
    input_path = temp_data_dir / 'input.parquet'
    output_path = temp_data_dir / 'output.parquet'
    
    sample_climate_data.to_parquet(input_path)
    
    metadata = run_imputation_pipeline(str(input_path), str(output_path))
    
    assert Path(output_path).exists()
    assert 'imputed_rows' in metadata
    assert metadata['imputed_rows'] == 2
    
    # Load and verify
    result_df = pd.read_parquet(output_path)
    assert 'is_imputed' in result_df.columns
    assert result_df['is_imputed'].sum() == 2


def test_run_imputation_pipeline_no_metadata(temp_data_dir):
    """Test pipeline with no missing values (no imputation needed)."""
    data = {
        'lat': [40.0, 40.5],
        'lon': [-75.0, -75.0],
        'temp': [15.0, 16.0],
        'week': [1, 1],
        'precip': [10.0, 12.0]
    }
    df = pd.DataFrame(data)
    
    input_path = temp_data_dir / 'input.parquet'
    output_path = temp_data_dir / 'output.parquet'
    
    df.to_parquet(input_path)
    
    metadata = run_imputation_pipeline(str(input_path), str(output_path))
    
    assert metadata['imputed_rows'] == 0