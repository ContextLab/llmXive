"""
Contract test for dataset schema (US1).

This test verifies that the dataset produced by the extraction and preprocessing
pipeline adheres to the strict schema requirements defined in the specification.
It ensures that all required columns exist, have the correct data types, and
that the data contains valid values for the specified event types.

Dependencies:
- T013: extract_latents.py (must produce raw Parquet)
- T014a-d: preprocess.py (must produce final Parquet)
"""

import os
import sys
import pytest
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any

# Add the project root to the path so we can import utils if needed
# (though this contract test primarily uses standard libraries and pandas)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Expected schema definition based on US1 requirements
# Columns: timestamp, semantic_feature, prosodic_feature, latent_delta_magnitude, turn_label
EXPECTED_COLUMNS = [
    "timestamp",
    "semantic_feature",
    "prosodic_feature",
    "latent_delta_magnitude",
    "turn_label"
]

# Expected data types for each column
EXPECTED_DTYPE_MAP = {
    "timestamp": "int64",           # Frame index or timestamp in ms
    "semantic_feature": "float32",  # Continuous vector or scalar feature
    "prosodic_feature": "float32",  # Continuous vector or scalar feature
    "latent_delta_magnitude": "float32", # Magnitude of change
    "turn_label": "category"        # Categorical: 'speaker_a', 'speaker_b', 'interruption', 'pause'
}

# Expected event types (turn_label values)
EXPECTED_EVENT_TYPES = {
    "interruption",
    "pause",
    "speaker_a",
    "speaker_b"
}

# Minimum sample size requirement
MIN_REQUIRED_SAMPLES = 10000

# Maximum allowed file size (1 GB in bytes)
MAX_FILE_SIZE_BYTES = 1024 * 1024 * 1024


def get_expected_output_path() -> Path:
    """
    Determines the expected path for the processed dataset Parquet file.
    Based on standard project conventions for US1 output.
    """
    # The path is relative to the project root
    # data/processed/ is the standard location for US1 output
    return PROJECT_ROOT / "data" / "processed" / "wan_streamer_latents.parquet"


def load_test_dataset() -> pd.DataFrame:
    """
    Loads the dataset produced by the pipeline.
    Raises FileNotFoundError if the file does not exist.
    """
    path = get_expected_output_path()
    if not path.exists():
        raise FileNotFoundError(
            f"Dataset file not found at {path}. "
            "Ensure T013 (extract_latents) and T014 (preprocess) have been executed."
        )
    return pd.read_parquet(path)


class TestDatasetSchema:
    """Contract tests for the US1 dataset schema."""

    def test_file_exists(self):
        """Verify that the output file exists on disk."""
        path = get_expected_output_path()
        assert path.exists(), f"Dataset file {path} does not exist."

    def test_file_size_constraint(self):
        """Verify that the output file is within the 1 GB size limit."""
        path = get_expected_output_path()
        file_size = path.stat().st_size
        assert file_size <= MAX_FILE_SIZE_BYTES, (
            f"Dataset file size ({file_size} bytes) exceeds limit ({MAX_FILE_SIZE_BYTES} bytes). "
            "Stratified sampling (T014b) may have failed to reduce size."
        )

    def test_required_columns_present(self):
        """Verify that all required columns are present in the dataset."""
        df = load_test_dataset()
        missing_cols = set(EXPECTED_COLUMNS) - set(df.columns)
        assert len(missing_cols) == 0, (
            f"Missing required columns: {missing_cols}. "
            f"Expected: {EXPECTED_COLUMNS}, Found: {list(df.columns)}"
        )

    def test_column_data_types(self):
        """Verify that columns have the expected data types."""
        df = load_test_dataset()
        errors = []
        for col, expected_dtype in EXPECTED_DTYPE_MAP.items():
            if col not in df.columns:
                continue # Already caught by column test

            actual_dtype = str(df[col].dtype)
            # Handle category vs object for turn_label if necessary, but we expect category
            if expected_dtype == "category":
                if not pd.api.types.is_categorical_dtype(df[col]):
                    errors.append(f"Column '{col}' is {actual_dtype}, expected 'category'")
            elif expected_dtype == "int64":
                if not pd.api.types.is_integer_dtype(df[col]):
                    errors.append(f"Column '{col}' is {actual_dtype}, expected 'int64'")
            elif "float" in expected_dtype:
                if not pd.api.types.is_float_dtype(df[col]):
                    errors.append(f"Column '{col}' is {actual_dtype}, expected '{expected_dtype}'")

        assert len(errors) == 0, f"Data type mismatches found:\n" + "\n".join(errors)

    def test_no_null_values(self):
        """Verify that no required columns contain null values."""
        df = load_test_dataset()
        null_counts = df[EXPECTED_COLUMNS].isnull().sum()
        non_zero_nulls = null_counts[null_counts > 0]

        assert len(non_zero_nulls) == 0, (
            f"Found null values in the following columns:\n{non_zero_nulls}. "
            "All required columns must be non-null."
        )

    def test_sample_size_minimum(self):
        """Verify that the dataset contains at least the minimum required samples."""
        df = load_test_dataset()
        count = len(df)
        assert count >= MIN_REQUIRED_SAMPLES, (
            f"Dataset contains {count} samples, which is less than the required minimum "
            f"of {MIN_REQUIRED_SAMPLES}. Ensure stratified sampling preserves sufficient data."
        )

    def test_event_types_valid(self):
        """Verify that turn_label values are within the expected set of event types."""
        df = load_test_dataset()
        unique_labels = set(df["turn_label"].unique())
        invalid_labels = unique_labels - EXPECTED_EVENT_TYPES

        assert len(invalid_labels) == 0, (
            f"Found invalid turn_label values: {invalid_labels}. "
            f"Allowed values: {EXPECTED_EVENT_TYPES}"
        )

    def test_latent_delta_non_negative(self):
        """Verify that latent_delta_magnitude is non-negative (as it is a magnitude)."""
        df = load_test_dataset()
        negative_count = (df["latent_delta_magnitude"] < 0).sum()
        assert negative_count == 0, (
            f"Found {negative_count} negative values in 'latent_delta_magnitude'. "
            "Magnitudes must be non-negative."
        )

    def test_timestamp_monotonicity_within_sessions(self):
        """
        Verify that timestamps are generally increasing within logical sessions.
        Note: This is a soft check; strict monotonicity might be broken by multi-threading
        or specific logging formats, but generally it should hold.
        """
        df = load_test_dataset()
        # Check if timestamps are sorted (assuming single session or sorted by session)
        # If the dataset has a 'session_id' column (not in schema but possible), we'd group by it.
        # For now, we just check that the overall range is sensible and non-decreasing
        # if the data is expected to be chronological.
        # Given the schema, we assume the data is a continuous stream or concatenated streams.
        # We check for massive backwards jumps which would indicate a bug.
        if len(df) > 1:
            diffs = df["timestamp"].diff()
            # Allow small negative diffs due to potential out-of-order logging,
            # but flag large negative jumps as errors.
            large_jumps = diffs < -1000 # Arbitrary threshold for 'large' backward jump
            assert large_jumps.sum() == 0, (
                "Detected large backward jumps in timestamp, indicating potential data corruption."
            )

if __name__ == "__main__":
    pytest.main([__file__, "-v"])