"""
Contract tests for data schema validation.
Tests that the ingestion pipeline correctly validates required columns
against the expected schema defined in the project specifications.
"""

import pytest
import pandas as pd
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ingestion.validate_data import validate_columns
from utils.config import get_project_root


class TestDataSchemaValidation:
    """Contract tests for schema validation of eye-tracking data."""

    @pytest.fixture
    def required_columns(self):
        """Return the list of required columns as defined in FR-002."""
        return [
            "fixation_duration",
            "saccade_amplitude",
            "gaze_distribution",
            "recall_accuracy",
            "valence_label"
        ]

    @pytest.fixture
    def valid_sample_data(self, required_columns):
        """Create a DataFrame with all required columns."""
        data = {
            "fixation_duration": [100.0, 150.0, 200.0],
            "saccade_amplitude": [5.0, 10.0, 15.0],
            "gaze_distribution": [0.2, 0.5, 0.8],
            "recall_accuracy": [0.85, 0.90, 0.75],
            "valence_label": ["positive", "neutral", "negative"]
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def invalid_sample_data_missing_columns(self):
        """Create a DataFrame missing required columns."""
        data = {
            "fixation_duration": [100.0, 150.0],
            "saccade_amplitude": [5.0, 10.0],
            # Missing: gaze_distribution, recall_accuracy, valence_label
        }
        return pd.DataFrame(data)

    def test_schema_validates_required_columns(self, valid_sample_data, required_columns):
        """
        Contract test: test_schema_validates_required_columns.
        
        Verifies that the validation function correctly identifies
        a DataFrame that contains all required columns.
        
        Expected behavior:
        - Function returns True
        - No missing columns are reported
        """
        result, missing_columns = validate_columns(valid_sample_data, required_columns)
        
        assert result is True, f"Schema validation should pass for valid data, but failed with missing: {missing_columns}"
        assert len(missing_columns) == 0, f"No columns should be missing, but found: {missing_columns}"

    def test_schema_fails_on_missing_columns(self, invalid_sample_data_missing_columns, required_columns):
        """
        Contract test: Schema validation should fail when required columns are missing.
        
        Verifies that the validation function correctly identifies
        a DataFrame that is missing required columns.
        
        Expected behavior:
        - Function returns False
        - Missing columns list contains the expected missing column names
        """
        result, missing_columns = validate_columns(invalid_sample_data_missing_columns, required_columns)
        
        assert result is False, "Schema validation should fail for data with missing columns"
        assert "gaze_distribution" in missing_columns
        assert "recall_accuracy" in missing_columns
        assert "valence_label" in missing_columns

    def test_schema_empty_dataframe(self, required_columns):
        """
        Contract test: Schema validation on an empty DataFrame.
        
        An empty DataFrame has the columns but no data. The column check
        should pass (columns exist), but this test verifies the function
        handles empty DataFrames without crashing.
        """
        empty_df = pd.DataFrame(columns=required_columns)
        result, missing_columns = validate_columns(empty_df, required_columns)
        
        assert result is True, "Schema validation should pass for empty DataFrame with correct columns"
        assert len(missing_columns) == 0

    def test_schema_extra_columns_ignored(self, required_columns):
        """
        Contract test: Extra columns should not cause validation failure.
        
        Verifies that the presence of additional, non-required columns
        does not affect the validation result.
        """
        data = {
            "fixation_duration": [100.0],
            "saccade_amplitude": [5.0],
            "gaze_distribution": [0.2],
            "recall_accuracy": [0.85],
            "valence_label": ["positive"],
            "extra_column_1": [123],
            "extra_column_2": ["test"]
        }
        df = pd.DataFrame(data)
        
        result, missing_columns = validate_columns(df, required_columns)
        
        assert result is True, "Schema validation should pass even with extra columns"
        assert len(missing_columns) == 0