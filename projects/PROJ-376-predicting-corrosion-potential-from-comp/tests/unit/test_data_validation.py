"""
Unit tests for schema validation logic in T014.

This test suite verifies that the schema validation logic in `code/utils/validation.py`
and `code/data/preprocess.py` correctly enforces data quality constraints:
1. Record count must be >= 500.
2. Critical fields (ph, temperature, potential_mV, alloy_id) must not be null.
3. Alloy diversity (specific_alloy_designation) must be >= 10.

These tests are designed to FAIL before T012-T017 implementation is complete,
ensuring the validation logic is actually implemented and working.
"""
import pytest
import pandas as pd
import json
from pathlib import Path
import tempfile
import os
import sys
from unittest.mock import patch, MagicMock

# Add project root to path if running standalone
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.exceptions import SchemaMismatchError
from utils.config import get_diagnostics_path
# Import the actual validation functions
from utils.validation import validate_record_count, validate_non_nulls, validate_alloy_diversity
from data.preprocess import validate_processed_data, write_count_report

class TestSchemaValidation:
    
    def create_mock_df(self, count: int, nulls: bool = False, alloys: int = 20):
        """Helper to create a mock dataframe with configurable parameters."""
        # Ensure we have enough unique alloy designations
        unique_designations = [f'spec_{i % alloys}' for i in range(count)]
        
        data = {
            'alloy_id': [f'alloy_{i}' for i in range(count)],
            'specific_alloy_designation': unique_designations,
            'ph': [7.0] * count,
            'temperature': [25.0] * count,
            'potential_mV': [100.0] * count,
            'composition': ['{}'] * count
        }
        
        if nulls:
            # Introduce nulls in a critical field (ph)
            data['ph'][0] = None
            # Also ensure the dataframe is properly typed
            data['ph'] = pd.array(data['ph'], dtype='float64')
            
        return pd.DataFrame(data)

    def test_validate_record_count_passes(self):
        """Test that record count validation passes with >= 500 records."""
        df = self.create_mock_df(count=500, nulls=False, alloys=20)
        is_valid, message = validate_record_count(df, min_count=500)
        assert is_valid is True
        assert "passed" in message.lower()

    def test_validate_record_count_fails_low_count(self):
        """Test that record count validation fails if count < 500."""
        df = self.create_mock_df(count=499, nulls=False, alloys=20)
        is_valid, message = validate_record_count(df, min_count=500)
        assert is_valid is False
        assert "below minimum threshold" in message.lower()

    def test_validate_non_nulls_passes(self):
        """Test that non-null validation passes when no nulls exist."""
        df = self.create_mock_df(count=600, nulls=False, alloys=20)
        is_valid, message = validate_non_nulls(df, critical_fields=['ph', 'temperature', 'potential_mV', 'alloy_id'])
        assert is_valid is True
        assert "passed" in message.lower()

    def test_validate_non_nulls_fails_nulls(self):
        """Test that non-null validation fails if critical fields contain nulls."""
        df = self.create_mock_df(count=600, nulls=True, alloys=20)
        is_valid, message = validate_non_nulls(df, critical_fields=['ph', 'temperature', 'potential_mV', 'alloy_id'])
        assert is_valid is False
        assert "null values found" in message.lower()

    def test_validate_alloy_diversity_passes(self):
        """Test that alloy diversity validation passes with >= 10 unique alloys."""
        df = self.create_mock_df(count=600, nulls=False, alloys=15)
        is_valid, message = validate_alloy_diversity(df, min_alloys=10)
        assert is_valid is True
        assert "passed" in message.lower()

    def test_validate_alloy_diversity_fails_low_alloys(self):
        """Test that alloy diversity validation fails if < 10 unique alloys."""
        df = self.create_mock_df(count=600, nulls=False, alloys=5)
        is_valid, message = validate_alloy_diversity(df, min_alloys=10)
        assert is_valid is False
        assert "insufficient alloy diversity" in message.lower()

    def test_full_validation_integration_passes(self):
        """Test the full validation pipeline with valid data."""
        df = self.create_mock_df(count=600, nulls=False, alloys=20)
        is_valid, message = validate_processed_data(df)
        assert is_valid is True
        assert "passed" in message.lower()

    def test_full_validation_integration_fails_low_count(self):
        """Test the full validation pipeline fails on low record count."""
        df = self.create_mock_df(count=499, nulls=False, alloys=20)
        is_valid, message = validate_processed_data(df)
        assert is_valid is False
        assert "below minimum threshold" in message.lower()

    def test_full_validation_integration_fails_nulls(self):
        """Test the full validation pipeline fails on null critical fields."""
        df = self.create_mock_df(count=600, nulls=True, alloys=20)
        is_valid, message = validate_processed_data(df)
        assert is_valid is False
        assert "null values found" in message.lower()

    def test_full_validation_integration_fails_low_alloys(self):
        """Test the full validation pipeline fails on low alloy diversity."""
        df = self.create_mock_df(count=600, nulls=False, alloys=5)
        is_valid, message = validate_processed_data(df)
        assert is_valid is False
        assert "insufficient alloy diversity" in message.lower()

    def test_count_report_written(self):
        """Test that count_report.txt is written correctly with valid JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = Path(tmpdir) / "count_report.txt"
            
            write_count_report(record_count=400, is_valid=False, output_path=report_path)
            
            assert report_path.exists()
            with open(report_path, 'r') as f:
                content = f.read()
                data = json.loads(content)
            
            assert data['actual_count'] == 400
            assert data['status'] == 'FAILED'
            assert data['threshold'] == 500
            assert 'timestamp' in data

    def test_schema_mismatch_error_raised_on_low_count(self):
        """Test that SchemaMismatchError is raised when record_count < 500."""
        df = self.create_mock_df(count=400, nulls=False, alloys=20)
        with pytest.raises(SchemaMismatchError) as exc_info:
            # Simulate the check that would happen in the pipeline
            is_valid, _ = validate_record_count(df, min_count=500)
            if not is_valid:
                raise SchemaMismatchError("Record count below minimum threshold")
        
        assert "Record count below minimum threshold" in str(exc_info.value)

    def test_schema_mismatch_error_raised_on_nulls(self):
        """Test that SchemaMismatchError is raised when critical fields are null."""
        df = self.create_mock_df(count=600, nulls=True, alloys=20)
        with pytest.raises(SchemaMismatchError) as exc_info:
            is_valid, _ = validate_non_nulls(df, critical_fields=['ph'])
            if not is_valid:
                raise SchemaMismatchError("Null values found in critical fields")
        
        assert "Null values found in critical fields" in str(exc_info.value)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])