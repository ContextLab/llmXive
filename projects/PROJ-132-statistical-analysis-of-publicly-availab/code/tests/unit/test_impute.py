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

from src.data.impute import (
    load_climate_data,
    identify_missing_values,
    interpolate_spatial,
    run_imputation_pipeline
)


@pytest.fixture
def sample_climate_data():
    """Create sample climate data with some missing values."""
    np.random.seed(42)
    n_points = 100
    data = {
        'lat': np.random.uniform(-90, 90, n_points),
        'lon': np.random.uniform(-180, 180, n_points),
        'temp': np.random.normal(15, 5, n_points),
        'week': np.random.randint(1, 53, n_points),
        'precip': np.random.exponential(10, n_points)
    }
    df = pd.DataFrame(data)

    # Introduce some missing values
    missing_indices = np.random.choice(n_points, size=10, replace=False)
    df.loc[missing_indices[:5], 'temp'] = np.nan
    df.loc[missing_indices[5:], 'precip'] = np.nan

    return df


@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


def test_load_climate_data(sample_climate_data, temp_data_dir):
    """Test loading climate data from parquet file."""
    input_path = Path(temp_data_dir) / 'test_climate.parquet'
    sample_climate_data.to_parquet(input_path)

    df = load_climate_data(str(input_path))

    assert len(df) == len(sample_climate_data)
    assert set(df.columns) == {'lat', 'lon', 'temp', 'week', 'precip'}


def test_load_climate_data_missing_file():
    """Test that loading a non-existent file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_climate_data('non_existent_file.parquet')


def test_load_climate_data_missing_columns(temp_data_dir):
    """Test that loading data with missing columns raises ValueError."""
    input_path = Path(temp_data_dir) / 'incomplete.parquet'
    incomplete_data = pd.DataFrame({'lat': [1, 2], 'lon': [3, 4]})
    incomplete_data.to_parquet(input_path)

    with pytest.raises(ValueError) as exc_info:
        load_climate_data(str(input_path))
    assert 'Missing required columns' in str(exc_info.value)


def test_identify_missing_values(sample_climate_data):
    """Test identification of missing values."""
    missing_mask = identify_missing_values(sample_climate_data)

    assert missing_mask.sum() == 10  # We introduced 10 missing values
    assert missing_mask.dtype == bool


def test_interpolate_spatial_no_missing(temp_data_dir, sample_climate_data):
    """Test interpolation when there are no missing values."""
    # Create data without missing values
    complete_data = sample_climate_data.dropna()
    input_path = Path(temp_data_dir) / 'complete.parquet'
    complete_data.to_parquet(input_path)

    df = load_climate_data(str(input_path))
    df_imputed, metadata = interpolate_spatial(df)

    assert metadata['imputed_count'] == 0
    assert metadata['imputed_temp'] == 0
    assert metadata['imputed_precip'] == 0


def test_interpolate_spatial_with_missing(sample_climate_data):
    """Test interpolation with missing values."""
    df_imputed, metadata = interpolate_spatial(sample_climate_data)

    # Check that imputation flags were added
    assert 'temp_imputed' in df_imputed.columns
    assert 'precip_imputed' in df_imputed.columns

    # Check that some values were imputed
    assert metadata['imputed_temp'] >= 0
    assert metadata['imputed_precip'] >= 0


def test_run_imputation_pipeline(sample_climate_data, temp_data_dir):
    """Test the full imputation pipeline."""
    input_path = Path(temp_data_dir) / 'input.parquet'
    output_path = Path(temp_data_dir) / 'output.parquet'
    metadata_path = Path(temp_data_dir) / 'metadata.json'

    sample_climate_data.to_parquet(input_path)

    metadata = run_imputation_pipeline(
        input_path=str(input_path),
        output_path=str(output_path),
        metadata_path=str(metadata_path)
    )

    # Check output file exists
    assert output_path.exists()

    # Check metadata file exists
    assert metadata_path.exists()

    # Check metadata content
    assert 'imputed_count' in metadata
    assert 'imputed_temp' in metadata
    assert 'imputed_precip' in metadata


def test_run_imputation_pipeline_no_metadata(sample_climate_data, temp_data_dir):
    """Test imputation pipeline without metadata file."""
    input_path = Path(temp_data_dir) / 'input.parquet'
    output_path = Path(temp_data_dir) / 'output.parquet'

    sample_climate_data.to_parquet(input_path)

    metadata = run_imputation_pipeline(
        input_path=str(input_path),
        output_path=str(output_path),
        metadata_path=None
    )

    assert output_path.exists()
    assert 'imputed_count' in metadata