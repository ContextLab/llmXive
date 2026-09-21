import pytest
import os
import json
import csv
import tempfile
from pathlib import Path
from datetime import datetime, timezone

# Import the functions we are testing
from src.cli.export_data import load_processed_data, export_to_csv, main
from src.utils.checksum import generate_checksum

class TestExportData:
    @pytest.fixture
    def sample_data(self):
        """Create a sample list of dependency dictionaries."""
        return [
            {
                "package_name": "lodash",
                "version": "4.17.21",
                "category": "utility",
                "last_release_date": "2021-01-01T00:00:00Z",
                "last_commit_date": "2021-02-01T00:00:00Z",
                "age_in_days": 365,
                "vulnerability_count": 0,
                "is_unmaintained": False,
                "source_repo": "https://github.com/lodash/lodash"
            },
            {
                "package_name": "express",
                "version": "4.18.2",
                "category": "framework",
                "last_release_date": "2022-05-01T00:00:00Z",
                "last_commit_date": "2022-06-01T00:00:00Z",
                "age_in_days": 180,
                "vulnerability_count": 2,
                "is_unmaintained": False,
                "source_repo": "https://github.com/expressjs/express"
            },
            {
                "package_name": "old-package",
                "version": "1.0.0",
                "category": "other",
                "last_release_date": None,  # Test null handling
                "last_commit_date": "2015-01-01T00:00:00Z",
                "age_in_days": None,       # Test null handling
                "vulnerability_count": 5,
                "is_unmaintained": True,
                "source_repo": "https://github.com/example/old"
            }
        ]

    @pytest.fixture
    def temp_input_file(self, sample_data):
        """Create a temporary JSON file with sample data."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample_data, f)
            return f.name

    @pytest.fixture
    def temp_output_file(self):
        """Create a temporary path for output file."""
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
            # Delete the file, we just want the path
            os.unlink(f.name)
            return f.name

    def test_load_processed_data_success(self, temp_input_file, sample_data):
        """Test loading data from a valid JSON file."""
        result = load_processed_data(temp_input_file)
        assert len(result) == len(sample_data)
        assert result[0]["package_name"] == "lodash"
        assert result[1]["vulnerability_count"] == 2

    def test_load_processed_data_file_not_found(self):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            load_processed_data("/nonexistent/path/data.json")

    def test_load_processed_data_invalid_format(self, temp_input_file):
        """Test that ValueError is raised for non-list JSON."""
        # Overwrite with non-list data
        with open(temp_input_file, 'w') as f:
            json.dump({"dependencies": []}, f) # This is actually handled by the function
        
        # Test truly invalid structure (dict without dependencies key)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"key": "value"}, f)
            invalid_file = f.name
        
        try:
            with pytest.raises(ValueError):
                load_processed_data(invalid_file)
        finally:
            os.unlink(invalid_file)

    def test_export_to_csv_creates_file(self, temp_input_file, temp_output_file):
        """Test that export_to_csv creates the output file."""
        checksum = export_to_csv(temp_input_file, temp_output_file)
        assert os.path.exists(temp_output_file)
        assert os.path.exists(temp_output_file + ".sha256") # Checksum file
        assert checksum is not None

    def test_export_to_csv_content(self, temp_input_file, temp_output_file):
        """Test that the CSV contains the expected headers and data."""
        export_to_csv(temp_input_file, temp_output_file)
        
        with open(temp_output_file, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) == 3
        headers = list(rows[0].keys())
        
        # Check for required headers
        required_headers = ["package_name", "age_in_days", "vulnerability_count", "last_release_date"]
        for header in required_headers:
            assert header in headers

    def test_export_to_csv_null_handling(self, temp_input_file, temp_output_file):
        """Test that null values are handled gracefully (written as empty string)."""
        export_to_csv(temp_input_file, temp_output_file)
        
        with open(temp_output_file, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        # The third row has null age_in_days and last_release_date
        old_pkg = [r for r in rows if r["package_name"] == "old-package"][0]
        assert old_pkg["age_in_days"] == ""
        assert old_pkg["last_release_date"] == ""
        assert old_pkg["vulnerability_count"] == "5" # Should be preserved

    def test_export_to_csv_checksum_verification(self, temp_input_file, temp_output_file):
        """Test that the generated checksum matches the file content."""
        checksum = export_to_csv(temp_input_file, temp_output_file)
        
        # Regenerate checksum from file
        regenerated = generate_checksum(temp_output_file)
        assert checksum == regenerated

    def test_export_to_csv_empty_data(self, temp_output_file):
        """Test that export_to_csv raises ValueError for empty data."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([], f)
            empty_file = f.name
        
        try:
            with pytest.raises(ValueError):
                export_to_csv(empty_file, temp_output_file)
        finally:
            os.unlink(empty_file)

    def test_main_function(self, temp_input_file, temp_output_file, capsys):
        """Test the main CLI entry point."""
        import sys
        sys.argv = ["export_data.py", "--input", temp_input_file, "--output", temp_output_file]
        
        try:
            main()
            captured = capsys.readouterr()
            assert "Successfully exported" in captured.out
            assert os.path.exists(temp_output_file)
        finally:
            sys.argv = []