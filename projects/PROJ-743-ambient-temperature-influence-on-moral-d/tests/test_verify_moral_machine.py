import os
import sys
import pytest
from pathlib import Path
import pandas as pd
from unittest.mock import patch, MagicMock

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from verify_moral_machine_source import verify_source_access, validate_schema, REQUIRED_COLUMNS

class TestMoralMachineVerification:
    def test_verify_source_access_success(self):
        """Test that a valid URL returns True."""
        with patch('verify_moral_machine_source.requests.head') as mock_head:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_head.return_value = mock_response
            
            result = verify_source_access("http://example.com/test.csv")
            assert result is True
            mock_head.assert_called_once()

    def test_verify_source_access_failure(self):
        """Test that a 404 URL returns False."""
        with patch('verify_moral_machine_source.requests.head') as mock_head:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_head.return_value = mock_response
            
            result = verify_source_access("http://example.com/missing.csv")
            assert result is False

    def test_validate_schema_pass(self, tmp_path):
        """Test schema validation with correct columns."""
        csv_path = tmp_path / "test.csv"
        # Create a CSV with required columns
        df = pd.DataFrame(columns=REQUIRED_COLUMNS)
        df.to_csv(csv_path, index=False)
        
        is_valid, missing = validate_schema(str(csv_path))
        assert is_valid is True
        assert missing == []

    def test_validate_schema_fail(self, tmp_path):
        """Test schema validation with missing columns."""
        csv_path = tmp_path / "test_missing.csv"
        # Create a CSV with only one required column
        df = pd.DataFrame(columns=['latitude'])
        df.to_csv(csv_path, index=False)
        
        is_valid, missing = validate_schema(str(csv_path))
        assert is_valid is False
        assert 'longitude' in missing
        assert 'timestamp' in missing
        assert 'response_time' in missing
        assert 'country' in missing
        assert 'dilemma_id' in missing

    def test_required_columns_defined(self):
        """Ensure REQUIRED_COLUMNS list is populated correctly."""
        assert len(REQUIRED_COLUMNS) == 6
        assert 'latitude' in REQUIRED_COLUMNS
        assert 'longitude' in REQUIRED_COLUMNS
        assert 'timestamp' in REQUIRED_COLUMNS
        assert 'response_time' in REQUIRED_COLUMNS
        assert 'country' in REQUIRED_COLUMNS
        assert 'dilemma_id' in REQUIRED_COLUMNS
