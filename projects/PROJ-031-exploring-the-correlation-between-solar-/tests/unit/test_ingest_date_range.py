import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock
import sys
import os

# Add code to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from ingest import validate_date_range, DataFetchError

class TestDateRangeValidation:
    
    def test_valid_range(self):
        """Test data that fully covers 2010-01-01 to 2023-12-31"""
        data = [
            {"date": "2010-01-01", "val": 1},
            {"date": "2023-12-31", "val": 2},
            {"date": "2020-06-15", "val": 3}
        ]
        result = validate_date_range(data, "TEST_SOURCE")
        assert result is True

    def test_start_date_slightly_off(self):
        """Test data starting 2 days late (Graceful failure)"""
        data = [
            {"date": "2010-01-03", "val": 1},
            {"date": "2023-12-31", "val": 2}
        ]
        # This should return False (limitation flag set) but not raise
        result = validate_date_range(data, "TEST_SOURCE")
        assert result is False

    def test_end_date_missing(self):
        """Test data ending before 2023-12-31 (Hard failure)"""
        data = [
            {"date": "2010-01-01", "val": 1},
            {"date": "2022-12-31", "val": 2}
        ]
        # This should return False (limitation flag set)
        result = validate_date_range(data, "TEST_SOURCE")
        assert result is False

    def test_empty_data(self):
        """Test with empty data list"""
        result = validate_date_range([], "TEST_SOURCE")
        assert result is False

    def test_invalid_date_format(self):
        """Test data with unparseable dates"""
        data = [
            {"date": "invalid", "val": 1},
            {"date": "2023-12-31", "val": 2}
        ]
        # Should skip invalid and check valid ones
        # If only one valid date (2023), it passes start but might fail if start < 2010
        # Here start is 2023, which is >= 2010, and end is 2023, which is >= 2023.
        # So it should pass if we only consider the valid one.
        result = validate_date_range(data, "TEST_SOURCE")
        assert result is True