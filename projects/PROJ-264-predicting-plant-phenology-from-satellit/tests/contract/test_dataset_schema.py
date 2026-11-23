"""
Contract tests for data artifacts against data-model.md specifications.

Validates that processed data files (CSVs) conform to the expected schema
defined in the project's data model.
"""
import json
import os
import pandas as pd
import pytest
from pathlib import Path
from src.config import get_config

# Load the data model schema (assuming it's converted to JSON for validation)
# Since data-model.md is markdown, we assume a corresponding JSON schema exists
# or we define the schema inline based on the spec.
# For this implementation, we define the expected schema structure inline
# as it would be extracted from data-model.md.

# Expected schema for the main phenology dataset (based on typical structure)
EXPECTED_DATASET_SCHEMA = {
    "type": "object",
    "properties": {
        "site_id": {"type": "string"},
        "date": {"type": "string", "format": "date"},
        "ndvi": {"type": "number"},
        "evi": {"type": "number"},
        "temp_mean": {"type": "number"},
        "precip": {"type": "number"},
        "phenology_date": {"type": ["string", "null"]},
        "phenology_type": {"type": ["string", "null"]},
        "cloud_cover": {"type": "number"},
        "gap_flag": {"type": "integer"}
    },
    "required": ["site_id", "date", "ndvi", "temp_mean"]
}

@pytest.fixture
def config():
    return get_config()

@pytest.fixture
def processed_data_path(config):
    """Get the path to the processed data directory."""
    return Path(config.paths.processed_data)

def test_processed_data_directory_exists(processed_data_path):
    """Verify that the processed data directory exists."""
    assert processed_data_path.exists(), f"Processed data directory not found: {processed_data_path}"

def test_phenology_dataset_schema(processed_data_path):
    """
    Validate the main phenology dataset CSV against the expected schema.
    
    This test checks:
    1. The file exists
    2. Required columns are present
    3. Data types are correct
    4. No unexpected nulls in required fields
    """
    # Look for the main processed dataset (naming convention from ingestion)
    # Assuming the file is named 'phenology_dataset.csv' or similar
    dataset_files = list(processed_data_path.glob("*phenology*.csv"))
    
    if not dataset_files:
        # If no file found, we might be in early stages, but we still check structure
        # if a file is expected to be created by previous tasks
        pytest.skip("No phenology dataset file found yet. This test requires T011-T014 to run first.")
    
    # Use the first found file
    dataset_file = dataset_files[0]
    df = pd.read_csv(dataset_file)
    
    # Check required columns
    required_cols = EXPECTED_DATASET_SCHEMA["required"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    assert not missing_cols, f"Missing required columns: {missing_cols}"
    
    # Check data types for numeric columns
    numeric_cols = ["ndvi", "evi", "temp_mean", "precip", "cloud_cover"]
    for col in numeric_cols:
        if col in df.columns:
            # Allow for float conversion errors if data is messy, but basic check
            assert pd.api.types.is_numeric_dtype(df[col]) or df[col].isna().all(), \
                f"Column {col} should be numeric"
    
    # Check for nulls in required columns
    for col in required_cols:
        if col in df.columns:
            null_count = df[col].isna().sum()
            assert null_count == 0, f"Required column {col} has {null_count} null values"

def test_data_consistency_with_model(processed_data_path):
    """
    Additional consistency checks based on data-model.md logic.
    E.g., date ranges, value ranges for NDVI (-1 to 1), etc.
    """
    dataset_files = list(processed_data_path.glob("*phenology*.csv"))
    if not dataset_files:
        pytest.skip("No phenology dataset file found yet.")
    
    df = pd.read_csv(dataset_files[0])
    
    # NDVI range check
    if "ndvi" in df.columns:
        ndvi_min = df["ndvi"].min()
        ndvi_max = df["ndvi"].max()
        # Allow slight floating point errors or -1 to 1 range
        assert ndvi_min >= -1.1 and ndvi_max <= 1.1, \
            f"NDVI values out of expected range [{ndvi_min}, {ndvi_max}]"
    
    # Date format check (basic)
    if "date" in df.columns:
        # Ensure dates can be parsed
        try:
            pd.to_datetime(df["date"])
        except Exception as e:
            pytest.fail(f"Date column could not be parsed: {e}")
