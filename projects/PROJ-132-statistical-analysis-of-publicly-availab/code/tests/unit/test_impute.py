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
    save_imputed_data,
    run_imputation_pipeline
)


@pytest.fixture
def sample_climate_data():
    """Create sample climate data with some missing values."""
    np.random.seed(42)
    n = 100
    df = pd.DataFrame({
        "lat": np.random.uniform(30, 50, n),
        "lon": np.random.uniform(-120, -70, n),
        "temp": np.random.normal(15, 5, n),
        "week": np.random.randint(1, 53, n),
        "precip": np.random.exponential(2, n)
    })
    # Introduce some missing values
    df.loc[0:4, "temp"] = np.nan
    df.loc[5:9, "precip"] = np.nan
    return df


@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    tmpdir = tempfile.mkdtemp()
    yield tmpdir
    shutil.rmtree(tmpdir)


def test_load_climate_data(sample_climate_data, temp_data_dir):
    """Test loading climate data from parquet file."""
    # Save sample data
    input_path = Path(temp_data_dir) / "climate.parquet"
    sample_climate_data.to_parquet(input_path)

    # Load data
    df = load_climate_data(str(input_path))

    # Verify
    assert len(df) == len(sample_climate_data)
    assert set(df.columns) == {"lat", "lon", "temp", "week", "precip"}


def test_load_climate_data_missing_file(temp_data_dir):
    """Test loading from non-existent file raises FileNotFoundError."""
    input_path = Path(temp_data_dir) / "nonexistent.parquet"
    with pytest.raises(FileNotFoundError):
        load_climate_data(str(input_path))


def test_load_climate_data_missing_columns(sample_climate_data, temp_data_dir):
    """Test loading data with missing columns raises ValueError."""
    # Create data with missing column
    incomplete_data = sample_climate_data.drop(columns=["temp"])
    input_path = Path(temp_data_dir) / "incomplete.parquet"
    incomplete_data.to_parquet(input_path)

    with pytest.raises(ValueError) as exc_info:
        load_climate_data(str(input_path))
    assert "temp" in str(exc_info.value)


def test_identify_missing_values(sample_climate_data):
    """Test identification of missing values."""
    df, missing_counts = identify_missing_values(sample_climate_data)

    assert "is_imputed" in df.columns
    assert missing_counts["temp"] == 5
    assert missing_counts["precip"] == 5
    assert df["is_imputed"].sum() == 0  # Not yet imputed


def test_interpolate_spatial_no_missing(temp_data_dir):
    """Test interpolation when no values are missing."""
    # Create complete data
    df = pd.DataFrame({
        "lat": [30.0, 31.0, 32.0],
        "lon": [-120.0, -119.0, -118.0],
        "temp": [15.0, 16.0, 17.0],
        "week": [1, 2, 3],
        "precip": [2.0, 3.0, 4.0]
    })

    df_interp = interpolate_spatial(df)

    # Values should remain unchanged
    assert df_interp["temp"].equals(df["temp"])
    assert df_interp["precip"].equals(df["precip"])
    assert df_interp["is_imputed"].sum() == 0


def test_interpolate_spatial_with_missing(sample_climate_data):
    """Test interpolation with missing values."""
    df = interpolate_spatial(sample_climate_data)

    # Check that missing values were filled (or marked as NaN if extrapolation)
    assert "is_imputed" in df.columns

    # Some values should be flagged as imputed
    imputed_count = df["is_imputed"].sum()
    assert imputed_count > 0

    # Original missing positions should now have values (or NaN if extrapolated)
    original_missing_temp = sample_climate_data["temp"].isna()
    # Either imputed or still NaN (if extrapolated)
    assert all(
        ~df.loc[original_missing_temp, "is_imputed"] | df.loc[original_missing_temp, "temp"].isna()
    )


def test_run_imputation_pipeline(sample_climate_data, temp_data_dir):
    """Test the full imputation pipeline."""
    # Setup paths
    input_path = Path(temp_data_dir) / "climate.parquet"
    output_path = Path(temp_data_dir) / "climate_imputed.parquet"
    metadata_path = Path(temp_data_dir) / "metadata.json"

    # Save input
    sample_climate_data.to_parquet(input_path)

    # Run pipeline
    result_df = run_imputation_pipeline(
        input_path=str(input_path),
        output_path=str(output_path),
        metadata_path=str(metadata_path)
    )

    # Verify output file exists
    assert output_path.exists()

    # Verify metadata file exists
    assert metadata_path.exists()

    # Verify result
    assert len(result_df) == len(sample_climate_data)
    assert "is_imputed" in result_df.columns


def test_run_imputation_pipeline_no_metadata(temp_data_dir):
    """Test pipeline with no missing data."""
    # Create complete data
    df = pd.DataFrame({
        "lat": [30.0, 31.0, 32.0, 33.0, 34.0],
        "lon": [-120.0, -119.0, -118.0, -117.0, -116.0],
        "temp": [15.0, 16.0, 17.0, 18.0, 19.0],
        "week": [1, 2, 3, 4, 5],
        "precip": [2.0, 3.0, 4.0, 5.0, 6.0]
    })

    input_path = Path(temp_data_dir) / "climate.parquet"
    output_path = Path(temp_data_dir) / "climate_imputed.parquet"
    metadata_path = Path(temp_data_dir) / "metadata.json"

    df.to_parquet(input_path)

    result_df = run_imputation_pipeline(
        input_path=str(input_path),
        output_path=str(output_path),
        metadata_path=str(metadata_path)
    )

    assert result_df["is_imputed"].sum() == 0
    assert output_path.exists()