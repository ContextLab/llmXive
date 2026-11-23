"""
Unit tests for code/data/validator.py (Task T010).

Tests verify that:
1. Missing data (N < 100) triggers InsufficientSampleError.
2. Empty data (N = 0) triggers DataGapError.
3. Missing longitudinal order (engagement_timestamp >= self_report_timestamp) triggers ValueError.
4. Valid data passes without error.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Import the function under test and the custom exceptions
from code.data.validator import validate_data
from code.utils.exceptions import DataGapError, InsufficientSampleError

# Constants for test data generation
BASE_TIMESTAMP = datetime(2023, 1, 1)

def create_valid_dataframe(n_rows=100, valid_order=True):
    """
    Helper to create a DataFrame that satisfies all validation requirements,
    optionally with invalid longitudinal ordering.
    """
    # Generate base timestamps
    if valid_order:
        # Engagement happens 1 day before self-report
        eng_ts = [BASE_TIMESTAMP - timedelta(days=1) for _ in range(n_rows)]
        rep_ts = [BASE_TIMESTAMP for _ in range(n_rows)]
    else:
        # Engagement happens 1 day AFTER self-report (Invalid)
        eng_ts = [BASE_TIMESTAMP + timedelta(days=1) for _ in range(n_rows)]
        rep_ts = [BASE_TIMESTAMP for _ in range(n_rows)]

    # Create a DataFrame with required columns
    df = pd.DataFrame({
        "engagement_count": np.random.randint(0, 100, n_rows),
        "sentiment_score": np.random.uniform(-1, 1, n_rows),
        "self_esteem_score": np.random.uniform(15, 30, n_rows),
        "perceived_social_validation": np.random.uniform(0, 1, n_rows),
        "engagement_timestamp": eng_ts,
        "self_report_timestamp": rep_ts,
        "age": np.random.randint(12, 18, n_rows),
        "gender": ["M", "F", "Other"] * (n_rows // 3) + ["M"] * (n_rows % 3),
        "offline_relationships": np.random.uniform(1, 5, n_rows),
        "intrinsic_traits": np.random.uniform(1, 5, n_rows),
    })
    return df

class TestValidatorSampleSize:
    """Tests for sample size validation (N=0 and N<100)."""

    def test_empty_dataset_raises_data_gap_error(self):
        """Verify that an empty DataFrame (N=0) raises DataGapError."""
        df = create_valid_dataframe(n_rows=0)
        with pytest.raises(DataGapError, match="Dataset is empty"):
            validate_data(df)

    def test_insufficient_sample_raises_insufficient_sample_error(self):
        """Verify that a small dataset (0 < N < 100) raises InsufficientSampleError."""
        # Create a dataset with 50 rows
        df = create_valid_dataframe(n_rows=50)
        with pytest.raises(InsufficientSampleError, match="insufficient"):
            validate_data(df)

    def test_minimum_sample_size_passes(self):
        """Verify that a dataset meeting the minimum sample size (N=100) passes."""
        df = create_valid_dataframe(n_rows=100)
        # Should not raise any exception
        result = validate_data(df)
        assert result is df

class TestValidatorLongitudinalOrder:
    """Tests for longitudinal ordering validation."""

    def test_invalid_longitudinal_order_raises_value_error(self):
        """Verify that engagement happening after self-report raises ValueError."""
        # Create a valid size dataset but with invalid timestamp order
        df = create_valid_dataframe(n_rows=100, valid_order=False)
        with pytest.raises(ValueError, match="Longitudinal ordering violation"):
            validate_data(df)

    def test_valid_longitudinal_order_passes(self):
        """Verify that correct timestamp order (engagement < self-report) passes."""
        df = create_valid_dataframe(n_rows=100, valid_order=True)
        result = validate_data(df)
        assert result is df

class TestValidatorRequiredColumns:
    """Tests for required column presence."""

    def test_missing_required_column_raises_value_error(self):
        """Verify that missing a required column raises ValueError."""
        df = create_valid_dataframe(n_rows=100)
        # Drop a required column
        df = df.drop(columns=["engagement_count"])
        with pytest.raises(ValueError, match="Missing required columns"):
            validate_data(df)

    def test_all_required_columns_present_passes(self):
        """Verify that a DataFrame with all required columns passes."""
        df = create_valid_dataframe(n_rows=100)
        # Ensure all required columns are present (they should be by creation)
        from code.data.validator import REQUIRED_COLUMNS
        assert all(col in df.columns for col in REQUIRED_COLUMNS)
        result = validate_data(df)
        assert result is df

class TestValidatorTimestampParsing:
    """Tests for timestamp parsing robustness."""

    def test_string_timestamps_are_parsed_correctly(self):
        """Verify that string timestamps are parsed and validated correctly."""
        df = create_valid_dataframe(n_rows=100, valid_order=True)
        # Convert datetime objects to ISO format strings
        df["engagement_timestamp"] = df["engagement_timestamp"].dt.isoformat()
        df["self_report_timestamp"] = df["self_report_timestamp"].dt.isoformat()

        # Should still pass as pandas.to_datetime handles ISO strings
        result = validate_data(df)
        assert result is df

    def test_invalid_timestamp_format_raises_value_error(self):
        """Verify that unparseable timestamp strings raise ValueError."""
        df = create_valid_dataframe(n_rows=100, valid_order=True)
        # Inject invalid timestamp strings
        df.loc[0, "engagement_timestamp"] = "not a date"
        df.loc[0, "self_report_timestamp"] = "also not a date"

        with pytest.raises(ValueError, match="Failed to parse timestamps"):
            validate_data(df)