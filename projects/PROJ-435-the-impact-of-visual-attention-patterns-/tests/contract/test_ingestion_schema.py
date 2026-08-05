"""
Contract test for data ingestion output schema (User Story 1).

This test verifies that the preprocessed gaze data output
conforms to the required schema.
"""
import os
import sys
import pytest
import pandas as pd
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / 'code'))

class TestIngestionSchema:
    """Test suite for ingestion schema contracts."""

    @pytest.fixture
    def expected_schema(self):
        """Define expected schema for preprocessed gaze data."""
        return {
            'participant_id': 'integer',
            'headline_id': 'integer',
            'fixation_duration': 'float',
            'roi_type': 'string'
        }

    def test_output_file_exists(self):
        """Test that the output file exists."""
        output_path = Path('data/derived/preprocessed_gaze.csv')
        assert output_path.exists(), f"Output file not found: {output_path}"

    def test_schema_compliance(self, expected_schema):
        """Test that output matches expected schema."""
        output_path = Path('data/derived/preprocessed_gaze.csv')
        
        if not output_path.exists():
            pytest.skip("Output file not yet generated")
        
        df = pd.read_csv(output_path)
        
        # Check required columns
        required_cols = list(expected_schema.keys())
        for col in required_cols:
            assert col in df.columns, f"Missing required column: {col}"
        
        # Check data types (approximate)
        assert df['participant_id'].dtype in ['int64', 'int32', 'float64']
        assert df['headline_id'].dtype in ['int64', 'int32', 'float64']
        assert df['fixation_duration'].dtype in ['float64', 'float32']
        assert df['roi_type'].dtype == 'object'  # string

    def test_no_null_values_in_required_fields(self):
        """Test that required fields have no null values."""
        output_path = Path('data/derived/preprocessed_gaze.csv')
        
        if not output_path.exists():
            pytest.skip("Output file not yet generated")
        
        df = pd.read_csv(output_path)
        required_cols = ['participant_id', 'headline_id', 'fixation_duration', 'roi_type']
        
        for col in required_cols:
            assert df[col].isna().sum() == 0, f"Column {col} contains null values"

    def test_roi_type_values_valid(self):
        """Test that roi_type values are from expected set."""
        output_path = Path('data/derived/preprocessed_gaze.csv')
        
        if not output_path.exists():
            pytest.skip("Output file not yet generated")
        
        df = pd.read_csv(output_path)
        valid_roi_types = ['source_attribution', 'other']
        
        invalid_values = df[~df['roi_type'].isin(valid_roi_types)]['roi_type'].unique()
        assert len(invalid_values) == 0, f"Invalid roi_type values found: {invalid_values}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])