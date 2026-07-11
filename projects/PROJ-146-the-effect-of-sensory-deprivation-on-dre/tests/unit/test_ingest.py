"""
Unit tests for data ingestion logic with missing metadata.

This module tests the ingest.py logic to ensure it handles
missing metadata fields gracefully, either by raising informative
errors or by auto-populating defaults where appropriate.
"""
import os
import sys
import tempfile
import pytest
import pandas as pd
from io import StringIO

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from ingest import detect_sensory_deprivation, validate_metadata, process_csv

class TestMissingMetadata:
    """Test cases for handling missing metadata in data ingestion."""

    @pytest.fixture
    def sample_csv_with_metadata(self):
        """Create a sample CSV with complete metadata."""
        csv_data = """participant_id,condition,recall,bizarreness,study_id,timestamp
        P001,strict (complete isolation),1,5,STUDY_001,2024-01-15
        P002,moderate (partial sensory reduction),0,3,STUDY_001,2024-01-15
        P003,partial (minimal sensory reduction),1,7,STUDY_001,2024-01-15"""
        return csv_data

    @pytest.fixture
    def sample_csv_missing_study_id(self):
        """Create a sample CSV missing study_id metadata."""
        csv_data = """participant_id,condition,recall,bizarreness,timestamp
        P001,strict (complete isolation),1,5,2024-01-15
        P002,moderate (partial sensory reduction),0,3,2024-01-15"""
        return csv_data

    @pytest.fixture
    def sample_csv_missing_timestamp(self):
        """Create a sample CSV missing timestamp metadata."""
        csv_data = """participant_id,condition,recall,bizarreness,study_id
        P001,strict (complete isolation),1,5,STUDY_001
        P002,moderate (partial sensory reduction),0,3,STUDY_001"""
        return csv_data

    @pytest.fixture
    def sample_csv_missing_all_metadata(self):
        """Create a sample CSV missing all optional metadata."""
        csv_data = """participant_id,condition,recall,bizarreness
        P001,strict (complete isolation),1,5
        P002,moderate (partial sensory reduction),0,3"""
        return csv_data

    def test_ingest_with_complete_metadata(self, sample_csv_with_metadata):
        """Test that ingestion works normally with complete metadata."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(sample_csv_with_metadata)
            temp_path = f.name

        try:
            df = process_csv(temp_path)
            assert df is not None
            assert 'study_id' in df.columns
            assert 'timestamp' in df.columns
            assert len(df) == 3
        finally:
            os.unlink(temp_path)

    def test_ingest_missing_study_id_autofill(self, sample_csv_missing_study_id):
        """Test that missing study_id is auto-filled with a default value."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(sample_csv_missing_study_id)
            temp_path = f.name

        try:
            df = process_csv(temp_path)
            assert df is not None
            assert 'study_id' in df.columns
            # Check that study_id was populated with a default
            assert df['study_id'].iloc[0] == 'UNKNOWN_STUDY'
            assert all(df['study_id'] == 'UNKNOWN_STUDY')
        finally:
            os.unlink(temp_path)

    def test_ingest_missing_timestamp_autofill(self, sample_csv_missing_timestamp):
        """Test that missing timestamp is auto-filled with current time."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(sample_csv_missing_timestamp)
            temp_path = f.name

        try:
            df = process_csv(temp_path)
            assert df is not None
            assert 'timestamp' in df.columns
            # Check that timestamp was populated (should be non-null)
            assert not df['timestamp'].isnull().any()
        finally:
            os.unlink(temp_path)

    def test_ingest_missing_all_metadata(self, sample_csv_missing_all_metadata):
        """Test ingestion when all optional metadata is missing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(sample_csv_missing_all_metadata)
            temp_path = f.name

        try:
            df = process_csv(temp_path)
            assert df is not None
            # Required columns must exist
            assert 'participant_id' in df.columns
            assert 'condition' in df.columns
            assert 'recall' in df.columns
            assert 'bizarreness' in df.columns
            # Optional columns should be auto-filled
            assert 'study_id' in df.columns
            assert 'timestamp' in df.columns
            assert df['study_id'].iloc[0] == 'UNKNOWN_STUDY'
        finally:
            os.unlink(temp_path)

    def test_validate_metadata_missing_required_fields(self):
        """Test validation when required fields are missing."""
        # Create a dataframe missing required fields
        df = pd.DataFrame({
            'recall': [1, 0],
            'bizarreness': [5, 3]
        })
        
        # Should raise ValueError for missing required fields
        with pytest.raises(ValueError) as exc_info:
            validate_metadata(df)
        
        assert 'participant_id' in str(exc_info.value)
        assert 'condition' in str(exc_info.value)

    def test_validate_metadata_missing_optional_fields(self):
        """Test validation when only optional fields are missing."""
        df = pd.DataFrame({
            'participant_id': ['P001', 'P002'],
            'condition': ['strict', 'moderate'],
            'recall': [1, 0],
            'bizarreness': [5, 3]
        })
        
        # Should not raise an error for missing optional fields
        # but should return a dict indicating which fields are missing
        result = validate_metadata(df)
        
        assert 'study_id' in result['missing_optional']
        assert 'timestamp' in result['missing_optional']
        assert result['missing_required'] == []

    def test_detect_sensory_deprivation_with_various_tags(self):
        """Test detection of sensory deprivation in various condition formats."""
        test_cases = [
            ('sensory_deprivation', True),
            ('deprivation', True),
            ('Sensory Deprivation', True),
            ('control', False),
            ('normal_sleep', False),
            ('partial_sensory_reduction', True),
            ('strict_isolation', True)
        ]
        
        for condition, expected in test_cases:
            result = detect_sensory_deprivation(condition)
            assert result == expected, f"Failed for condition: {condition}"

    def test_process_csv_empty_file(self):
        """Test processing an empty CSV file."""
        csv_data = ""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_data)
            temp_path = f.name

        try:
            with pytest.raises(ValueError) as exc_info:
                process_csv(temp_path)
            assert "empty" in str(exc_info.value).lower()
        finally:
            os.unlink(temp_path)

    def test_process_csv_missing_required_columns(self):
        """Test processing a CSV missing required columns."""
        csv_data = """participant_id,recall
        P001,1
        P002,0"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_data)
            temp_path = f.name

        try:
            with pytest.raises(ValueError) as exc_info:
                process_csv(temp_path)
            assert "condition" in str(exc_info.value)
        finally:
            os.unlink(temp_path)

    def test_ingest_with_null_values_in_required_fields(self):
        """Test ingestion when required fields contain null values."""
        csv_data = """participant_id,condition,recall,bizarreness
        P001,,1,5
        P002,strict,0,3"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_data)
            temp_path = f.name

        try:
            with pytest.raises(ValueError) as exc_info:
                process_csv(temp_path)
            assert "null" in str(exc_info.value).lower() or "missing" in str(exc_info.value).lower()
        finally:
            os.unlink(temp_path)