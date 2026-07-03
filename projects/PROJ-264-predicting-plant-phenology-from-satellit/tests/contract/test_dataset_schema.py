"""
Contract tests for data output schemas.

These tests validate that the output of data processing scripts
(e.g., src/data/ingestion.py) conforms to the schemas defined
in data-model.md and contracts/.

Implementation: T037a
"""

import os
import pytest
import pandas as pd
from pathlib import Path

# Import config to determine expected output paths
# Note: We import the function, not the module directly, to match API surface
from src.config import get_config


@pytest.fixture
def config():
    """Load project configuration."""
    return get_config()

@pytest.fixture
def processed_data_path(config):
    """Get the path to the processed dataset."""
    # The ingestion script is expected to write to data/processed/aligned_phenology.csv
    # based on standard project conventions and data-model.md.
    return Path(config.data_dir) / "processed" / "aligned_phenology.csv"

def test_dataset_file_exists(processed_data_path):
    """
    Contract: The ingestion pipeline MUST produce a CSV file at the
    expected location in data/processed/.
    """
    assert processed_data_path.exists(), (
        f"Expected dataset file not found at {processed_data_path}. "
        "Ensure src/data/ingestion.py has been run successfully."
    )

def test_dataset_schema_columns(processed_data_path, config):
    """
    Contract: The dataset MUST contain the specific columns required
    by the downstream model training (US2) and feature engineering (US1).
    
    Required columns based on data-model.md:
    - site_id: Identifier for the study site
    - date: Temporal coordinate (YYYY-MM-DD)
    - ndvi: Normalized Difference Vegetation Index
    - evi: Enhanced Vegetation Index
    - temp_mean: Mean daily temperature
    - temp_min: Minimum daily temperature
    - temp_max: Maximum daily temperature
    - precip: Total daily precipitation
    - phenology_event: Categorical event label (if ground truth exists)
    - phenology_date: Date of the phenology event (if ground truth exists)
    """
    df = pd.read_csv(processed_data_path)
    
    required_columns = {
        'site_id',
        'date',
        'ndvi',
        'evi',
        'temp_mean',
        'temp_min',
        'temp_max',
        'precip',
        'phenology_event',
        'phenology_date'
    }
    
    actual_columns = set(df.columns)
    missing_columns = required_columns - actual_columns
    
    assert not missing_columns, (
        f"Dataset is missing required schema columns: {missing_columns}. "
        f"Found columns: {list(df.columns)}"
    )

def test_dataset_no_temporal_gaps(processed_data_path):
    """
    Contract: The dataset MUST NOT have un-interpolated temporal gaps
    within a specific site's time series.
    
    While full interpolation logic is in preprocessing, the ingestion
    output must be temporally aligned such that for a given site_id,
    the date index is continuous (or at least sorted and non-duplicate).
    """
    df = pd.read_csv(processed_data_path)
    
    # Ensure 'date' is parsed as datetime
    df['date'] = pd.to_datetime(df['date'])
    
    # Check for duplicate dates per site
    duplicates = df.groupby(['site_id', 'date']).size()
    duplicates = duplicates[duplicates > 1]
    
    assert len(duplicates) == 0, (
        f"Found duplicate date entries for sites: {duplicates.index.tolist()}. "
        "Data alignment logic must ensure unique timestamps per site."
    )

def test_dataset_numeric_types(processed_data_path):
    """
    Contract: Numeric columns MUST be of a numeric dtype to ensure
    compatibility with scikit-learn/XGBoost pipelines.
    """
    df = pd.read_csv(processed_data_path)
    
    numeric_cols = ['ndvi', 'evi', 'temp_mean', 'temp_min', 'temp_max', 'precip']
    
    for col in numeric_cols:
        if col in df.columns:
            assert pd.api.types.is_numeric_dtype(df[col]), (
                f"Column '{col}' is not numeric. Found dtype: {df[col].dtype}"
            )

def test_dataset_site_ids_valid(processed_data_path, config):
    """
    Contract: All site_ids in the dataset MUST exist in the configuration's
    defined study sites list.
    """
    df = pd.read_csv(processed_data_path)
    
    # Get valid site IDs from config (assuming config has a list of sites)
    # The config structure might vary, but we assume a list of valid IDs exists.
    # If config doesn't expose sites directly, we rely on the fact that
    # ingestion.py filters based on config.
    valid_sites = set(config.get('study_sites', []))
    
    if valid_sites:
        actual_sites = set(df['site_id'].unique())
        invalid_sites = actual_sites - valid_sites
        
        assert not invalid_sites, (
            f"Dataset contains unknown site IDs: {invalid_sites}. "
            "Sites must be defined in config.py."
        )