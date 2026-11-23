"""
Contract test for data ingestion output schema (User Story 1).

This test verifies that the preprocessed gaze data output
conforms to the required schema as defined in the project specification.
It ensures that the preprocessing pipeline (T018) produces data with the
correct columns, types, and valid ROI values.
"""
import os
import sys
import pytest
import pandas as pd
from pathlib import Path

# Add code directory to path to resolve imports if needed,
# though this test primarily relies on file system checks.
_code_path = Path(__file__).resolve().parent.parent.parent / 'code'
if str(_code_path) not in sys.path:
    sys.path.insert(0, str(_code_path))

class TestIngestionSchema:
    """Test suite for ingestion schema contracts."""

    @pytest.fixture
    def expected_schema(self):
        """Define expected schema for preprocessed gaze data."""
        # Based on T018 requirements and data-model.md
        return {
            'participant_id': 'integer',
            'headline_id': 'integer',
            'fixation_duration': 'float',
            'roi_type': 'string'
        }

    def test_output_file_exists(self):
        """Test that the output file exists."""
        output_path = Path('data/derived/preprocessed_gaze.csv')
        assert output_path.exists(), f"Output file not found: {output_path}. " \
                                     "Ensure T018 (02_preprocess_gaze.py) has run successfully."

    def test_schema_compliance(self, expected_schema):
        """Test that output matches expected schema."""
        output_path = Path('data/derived/preprocessed_gaze.csv')
        
        if not output_path.exists():
            pytest.skip("Output file not yet generated")
        
        df = pd.read_csv(output_path)
        
        # Check required columns
        required_cols = list(expected_schema.keys())
        missing_cols = [col for col in required_cols if col not in df.columns]
        assert not missing_cols, f"Missing required columns: {missing_cols}"
        
        # Check data types (approximate to allow for platform differences)
        # participant_id and headline_id should be integer-like
        assert df['participant_id'].dtype in ['int64', 'int32', 'float64', 'float32'], \
            f"participant_id has unexpected dtype: {df['participant_id'].dtype}"
        
        assert df['headline_id'].dtype in ['int64', 'int32', 'float64', 'float32'], \
            f"headline_id has unexpected dtype: {df['headline_id'].dtype}"
        
        # fixation_duration should be float
        assert df['fixation_duration'].dtype in ['float64', 'float32'], \
            f"fixation_duration has unexpected dtype: {df['fixation_duration'].dtype}"
        
        # roi_type should be string/object
        assert df['roi_type'].dtype == 'object', \
            f"roi_type has unexpected dtype: {df['roi_type'].dtype}"

    def test_no_null_values_in_required_fields(self):
        """Test that required fields have no null values."""
        output_path = Path('data/derived/preprocessed_gaze.csv')
        
        if not output_path.exists():
            pytest.skip("Output file not yet generated")
        
        df = pd.read_csv(output_path)
        required_cols = ['participant_id', 'headline_id', 'fixation_duration', 'roi_type']
        
        for col in required_cols:
            null_count = df[col].isna().sum()
            assert null_count == 0, f"Column '{col}' contains {null_count} null values"

    def test_roi_type_values_valid(self):
        """Test that roi_type values are from expected set."""
        output_path = Path('data/derived/preprocessed_gaze.csv')
        
        if not output_path.exists():
            pytest.skip("Output file not yet generated")
        
        df = pd.read_csv(output_path)
        # Valid ROIs defined in code/config.yaml and used in T015/T018
        valid_roi_types = ['source_attribution', 'headline_body', 'other']
        
        # Filter for non-null values first (though test_no_null_values should catch nulls)
        non_null_roi = df['roi_type'].dropna()
        invalid_values = non_null_roi[~non_null_roi.isin(valid_roi_types)].unique()
        
        assert len(invalid_values) == 0, f"Invalid roi_type values found: {invalid_values}. " \
                                         f"Expected one of: {valid_roi_types}"

    def test_data_integrity_sample(self):
        """Basic sanity check on data distribution."""
        output_path = Path('data/derived/preprocessed_gaze.csv')
        
        if not output_path.exists():
            pytest.skip("Output file not yet generated")
        
        df = pd.read_csv(output_path)
        
        # Check that we have some data
        assert len(df) > 0, "Preprocessed gaze data is empty"
        
        # Check that fixation durations are non-negative
        assert (df['fixation_duration'] >= 0).all(), "Found negative fixation durations"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])