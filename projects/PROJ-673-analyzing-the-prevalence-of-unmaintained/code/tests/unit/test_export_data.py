import pytest
import os
import json
import csv
import tempfile
from pathlib import Path
from datetime import datetime, timezone

# Import the module under test
from src.cli.export_data import load_processed_data, export_to_csv

class TestExportData:
    
    @pytest.fixture
    def temp_json_file(self, tmp_path):
        """Create a temporary JSON file with sample processed data."""
        sample_data = [
            {
                "package_name": "pkg-a",
                "version": "1.0.0",
                "dependency_name": "dep-x",
                "dependency_version": "2.0.0",
                "last_release_date": "2023-01-01T00:00:00+00:00",
                "last_commit_date": "2023-06-01T00:00:00+00:00",
                "age_in_days": 100,
                "vulnerability_count": 2,
                "is_unmaintained": False,
                "category": "utility"
            },
            {
                "package_name": "pkg-b",
                "version": "3.0.0",
                "dependency_name": "dep-y",
                "dependency_version": "1.1.0",
                "last_release_date": None,
                "last_commit_date": "2022-01-01T00:00:00+00:00",
                "age_in_days": None,  # Null age as per T017
                "vulnerability_count": 0,
                "is_unmaintained": True,
                "category": "framework"
            }
        ]
        file_path = tmp_path / "test_data.json"
        with open(file_path, 'w') as f:
            json.dump(sample_data, f)
        return file_path

    @pytest.fixture
    def temp_output_dir(self, tmp_path):
        """Create a temporary directory for output."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        return output_dir

    def test_load_processed_data_success(self, temp_json_file):
        """Test loading data from a valid JSON file."""
        data = load_processed_data(str(temp_json_file))
        assert len(data) == 2
        assert data[0]["package_name"] == "pkg-a"
        assert data[1]["age_in_days"] is None

    def test_load_processed_data_not_found(self, tmp_path):
        """Test loading data from a non-existent file raises error."""
        with pytest.raises(FileNotFoundError):
            load_processed_data(str(tmp_path / "nonexistent.json"))

    def test_export_to_csv_with_null_age(self, temp_json_file, temp_output_dir):
        """Test that export_to_csv handles null age_in_days correctly."""
        output_path = temp_output_dir / "test_output.csv"
        data = load_processed_data(str(temp_json_file))
        
        export_to_csv(data, str(output_path))
        
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) == 2
        # Check first row
        assert rows[0]["age_in_days"] == "100"
        assert rows[0]["vulnerability_count"] == "2"
        # Check second row (null age)
        assert rows[1]["age_in_days"] == "" # Empty string for null
        assert rows[1]["vulnerability_count"] == "0"

    def test_export_to_csv_empty_data(self, temp_output_dir):
        """Test that exporting empty data raises an error."""
        output_path = temp_output_dir / "empty.csv"
        with pytest.raises(ValueError, match="No data to export"):
            export_to_csv([], str(output_path))
    
    def test_export_creates_directory(self, temp_json_file, tmp_path):
        """Test that export_to_csv creates parent directories if they don't exist."""
        deep_path = tmp_path / "deep" / "nested" / "output.csv"
        data = load_processed_data(str(temp_json_file))
        
        export_to_csv(data, str(deep_path))
        
        assert deep_path.exists()