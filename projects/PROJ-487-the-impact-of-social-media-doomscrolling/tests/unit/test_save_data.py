"""
Unit tests for the data saving logic (T015).
"""
import os
import sys
import csv
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from save_data import write_csv

class TestWriteCSV:
    def test_write_gdelt_data(self, tmp_path):
        """Test writing GDELT schema data."""
        data = [
            {"date": "2023-01-01", "value": -50.0, "source": "GDELT"},
            {"date": "2023-01-02", "value": -45.0, "source": "GDELT"}
        ]
        filepath = tmp_path / "gdelt_test.csv"
        
        result = write_csv(filepath, data, "gdelt")
        
        assert result is True
        assert filepath.exists()
        
        with open(filepath, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 2
            assert rows[0]["date"] == "2023-01-01"
            assert float(rows[0]["value"]) == -50.0
            assert rows[0]["source"] == "GDELT"

    def test_write_trends_data(self, tmp_path):
        """Test writing Trends schema data."""
        data = [
            {"date": "2023-01-01", "value": 12.0, "source": "Google Trends"},
            {"date": "2023-01-02", "value": 15.0, "source": "Google Trends"}
        ]
        filepath = tmp_path / "trends_test.csv"
        
        result = write_csv(filepath, data, "trends")
        
        assert result is True
        assert filepath.exists()
        
        with open(filepath, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 2
            assert rows[0]["value"] == "12.0" # CSV reads as string

    def test_empty_data(self, tmp_path):
        """Test handling of empty data list."""
        data = []
        filepath = tmp_path / "empty_test.csv"
        
        # Should return False and log warning (mocked elsewhere or just check return)
        result = write_csv(filepath, data, "gdelt")
        
        # Based on implementation, it returns False for empty data
        assert result is False
        assert filepath.exists() # It creates file with headers

    def test_missing_required_fields(self, tmp_path):
        """Test handling of missing required fields."""
        data = [
            {"date": "2023-01-01", "value": -50.0} # Missing source
        ]
        filepath = tmp_path / "bad_schema_test.csv"
        
        result = write_csv(filepath, data, "gdelt")
        
        assert result is False
        # File might not be written or written partially, but function returns False
