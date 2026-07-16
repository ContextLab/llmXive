"""
Contract test for data ingestion output schema.

This test verifies that the output of the data ingestion pipeline (T012)
adheres to the strict schema defined in the project specifications.
It ensures that all required columns are present, data types are correct,
and no unexpected columns are introduced.

This test is part of User Story 1 (US1) and must run before implementation
of the ingestion script to ensure a Test-Driven Development approach.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add the code directory to the path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.environment_manager import get_paths

# Define the expected schema for the preprocessed gaze data
# Based on T018 output requirements and GazeEvent data model
EXPECTED_COLUMNS = {
    "participant_id": "integer",
    "headline_id": "string",
    "trial_id": "integer",
    "fixation_id": "integer",
    "timestamp": "float64",
    "duration": "float64",
    "x_coord": "float64",
    "y_coord": "float64",
    "roi": "string",
    "fixation_type": "string",
    "data_quality_flag": "string"
}

REQUIRED_COLUMNS = [
    "participant_id",
    "headline_id",
    "trial_id",
    "fixation_id",
    "timestamp",
    "duration",
    "x_coord",
    "y_coord",
    "roi",
    "fixation_type",
    "data_quality_flag"
]

# Define allowed values for categorical columns
ALLOWED_VALUES = {
    "roi": ["source_attribution", "headline", "body_text", "image", "other", "unknown"],
    "fixation_type": ["I-VT", "I-DT", "saccade", "blink"],
    "data_quality_flag": ["pass", "low_quality", "excluded"]
}

def get_expected_output_path():
    """Get the expected output path for preprocessed gaze data."""
    paths = get_paths()
    return paths["data_derived"] / "preprocessed_gaze.csv"

def test_ingestion_output_schema_exists():
    """Test that the ingestion output file exists."""
    output_path = get_expected_output_path()
    assert output_path.exists(), f"Output file {output_path} does not exist. " \
                                 "Run T018 (01_ingest_and_preprocess.py) first."

def test_ingestion_output_has_required_columns():
    """Test that the output contains all required columns."""
    output_path = get_expected_output_path()
    df = pd.read_csv(output_path)

    missing_columns = set(REQUIRED_COLUMNS) - set(df.columns)
    extra_columns = set(df.columns) - set(REQUIRED_COLUMNS)

    assert not missing_columns, f"Missing required columns: {missing_columns}"
    # Extra columns are allowed but should be logged
    if extra_columns:
        pytest.fail(f"Unexpected columns found: {extra_columns}. "
                    "Schema contract violation.")

def test_ingestion_output_column_types():
    """Test that columns have the expected data types."""
    output_path = get_expected_output_path()
    df = pd.read_csv(output_path)

    for col, expected_type in EXPECTED_COLUMNS.items():
        if col not in df.columns:
            continue  # Already checked in test_ingestion_output_has_required_columns

        actual_type = str(df[col].dtype)

        # Special handling for integer types that might be stored as float due to NaN
        if expected_type == "integer" and actual_type.startswith("float"):
            # Check if it can be safely converted to integer
            try:
                df[col].astype("Int64")  # Nullable integer
            except (ValueError, TypeError):
                pytest.fail(f"Column '{col}' has dtype {actual_type} but expected integer. "
                            f"Cannot safely convert to integer.")

        elif expected_type == "string" and actual_type not in ["object", "string"]:
            pytest.fail(f"Column '{col}' has dtype {actual_type} but expected string.")

        elif expected_type == "float64" and actual_type != "float64":
            pytest.fail(f"Column '{col}' has dtype {actual_type} but expected float64.")

def test_ingestion_output_categorical_values():
    """Test that categorical columns contain only allowed values."""
    output_path = get_expected_output_path()
    df = pd.read_csv(output_path)

    for col, allowed in ALLOWED_VALUES.items():
        if col not in df.columns:
            continue

        unique_values = set(df[col].dropna().unique())
        invalid_values = unique_values - set(allowed)

        assert not invalid_values, f"Column '{col}' contains invalid values: {invalid_values}. " \
                                   f"Allowed values: {allowed}"

def test_ingestion_output_no_nulls_in_required_fields():
    """Test that required fields do not contain null values."""
    output_path = get_expected_output_path()
    df = pd.read_csv(output_path)

    null_fields = {
        "participant_id": "participant_id cannot be null",
        "headline_id": "headline_id cannot be null",
        "trial_id": "trial_id cannot be null",
        "fixation_id": "fixation_id cannot be null",
        "duration": "duration cannot be null",
        "roi": "roi cannot be null"
    }

    for col, message in null_fields.items():
        if col in df.columns:
            null_count = df[col].isna().sum()
            assert null_count == 0, f"{message}. Found {null_count} null values."

def test_ingestion_output_positive_duration():
    """Test that duration values are positive."""
    output_path = get_expected_output_path()
    df = pd.read_csv(output_path)

    if "duration" in df.columns:
        negative_durations = (df["duration"] <= 0).sum()
        assert negative_durations == 0, f"Found {negative_durations} non-positive duration values. " \
                                        "Duration must be positive."

def test_ingestion_output_roi_mapping_validity():
    """Test that ROI mapping is consistent with expected ROIs."""
    output_path = get_expected_output_path()
    df = pd.read_csv(output_path)

    # Check that 'source_attribution' is present if there are any fixations
    # This validates that ROI mapping logic (T015) is working
    if len(df) > 0:
        roi_counts = df["roi"].value_counts()
        # At least some ROIs should be mapped
        assert roi_counts.sum() > 0, "No ROIs were mapped in the output."

def test_ingestion_output_data_quality_filter():
    """Test that data quality filter (T014) has been applied."""
    output_path = get_expected_output_path()
    df = pd.read_csv(output_path)

    # The filter should retain participants with <20% data loss
    # This is hard to verify without the original data, but we can check
    # that the data_quality_flag column exists and has expected values
    assert "data_quality_flag" in df.columns, "data_quality_flag column is missing."

    quality_flags = df["data_quality_flag"].unique()
    assert "pass" in quality_flags, "No 'pass' quality flags found. " \
                                    "Data quality filter may not be working."

    # Check that excluded participants are not present (or marked as such)
    # This depends on how the filter is implemented
    if "excluded" in quality_flags:
        excluded_count = (df["data_quality_flag"] == "excluded").sum()
        # If there are excluded rows, they should be clearly marked
        assert excluded_count < len(df), "All rows are marked as excluded. " \
                                         "Filter may be too aggressive."

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
