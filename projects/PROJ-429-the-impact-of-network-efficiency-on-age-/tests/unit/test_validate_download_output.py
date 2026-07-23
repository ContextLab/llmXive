"""
Unit tests for validate_download_output.py
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Import the functions to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from validate_download_output import validate_schema, validate_raw_directory_structure, validate_report_file

class TestValidateSchema:
    def test_valid_schema(self):
        """Test that a valid report schema passes."""
        valid_report = {
            "valid_count": 100,
            "invalid_instrument_count": 10,
            "missing_cognitive_count": 5,
            "total_count": 115
        }
        is_valid, errors = validate_schema(valid_report)
        assert is_valid is True
        assert len(errors) == 0

    def test_missing_key(self):
        """Test that missing keys are detected."""
        invalid_report = {
            "valid_count": 100,
            "total_count": 100
        }
        is_valid, errors = validate_schema(invalid_report)
        assert is_valid is False
        assert "Missing required key: invalid_instrument_count" in errors
        assert "Missing required key: missing_cognitive_count" in errors

    def test_wrong_type(self):
        """Test that wrong types are detected."""
        invalid_report = {
            "valid_count": "100",  # Should be int
            "invalid_instrument_count": 10,
            "missing_cognitive_count": 5,
            "total_count": 115
        }
        is_valid, errors = validate_schema(invalid_report)
        assert is_valid is False
        assert any("wrong type" in err for err in errors)

    def test_negative_value(self):
        """Test that negative values are detected."""
        invalid_report = {
            "valid_count": -10,
            "invalid_instrument_count": 10,
            "missing_cognitive_count": 5,
            "total_count": 5
        }
        is_valid, errors = validate_schema(invalid_report)
        assert is_valid is False
        assert any("negative value" in err for err in errors)

    def test_count_mismatch(self):
        """Test that count mismatch is detected."""
        invalid_report = {
            "valid_count": 100,
            "invalid_instrument_count": 10,
            "missing_cognitive_count": 5,
            "total_count": 200  # Should be 115
        }
        is_valid, errors = validate_schema(invalid_report)
        assert is_valid is False
        assert any("Count mismatch" in err for err in errors)

    def test_not_dict(self):
        """Test that non-dict input is detected."""
        is_valid, errors = validate_schema("not a dict")
        assert is_valid is False
        assert "Report data is not a dictionary" in errors

class TestValidateRawDirectoryStructure:
    def test_directory_not_exists(self):
        """Test that non-existent directory is detected."""
        is_valid, errors = validate_raw_directory_structure(Path("/nonexistent/path"))
        assert is_valid is False
        assert "does not exist" in errors[0]

    def test_no_subdirectories(self):
        """Test that empty directory is detected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            is_valid, errors = validate_raw_directory_structure(Path(tmpdir))
            assert is_valid is False
            assert "No subdirectories found" in errors[0]

    def test_no_eeg_files(self):
        """Test that directory without EEG files is detected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a dummy subdirectory
            os.makedirs(Path(tmpdir) / "abnormal")
            is_valid, errors = validate_raw_directory_structure(Path(tmpdir))
            assert is_valid is False
            assert "No EEG files" in errors[0]

    def test_valid_structure(self):
        """Test that valid structure passes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create valid structure
            abnormal_dir = Path(tmpdir) / "abnormal"
            abnormal_dir.mkdir()
            # Create a dummy EEG file
            eeg_file = abnormal_dir / "dummy.edf"
            eeg_file.write_text("dummy")
            
            is_valid, errors = validate_raw_directory_structure(Path(tmpdir))
            assert is_valid is True
            assert len(errors) == 0

class TestValidateReportFile:
    def test_file_not_exists(self):
        """Test that non-existent file is detected."""
        is_valid, errors = validate_report_file(Path("/nonexistent/report.json"))
        assert is_valid is False
        assert "does not exist" in errors[0]

    def test_invalid_json(self):
        """Test that invalid JSON is detected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = Path(tmpdir) / "report.json"
            report_path.write_text("invalid json {")
            
            is_valid, errors = validate_report_file(report_path)
            assert is_valid is False
            assert "Invalid JSON" in errors[0]

    def test_valid_report(self):
        """Test that valid report file passes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = Path(tmpdir) / "report.json"
            valid_report = {
                "valid_count": 100,
                "invalid_instrument_count": 10,
                "missing_cognitive_count": 5,
                "total_count": 115
            }
            with open(report_path, 'w') as f:
                json.dump(valid_report, f)
            
            is_valid, errors = validate_report_file(report_path)
            assert is_valid is True
            assert len(errors) == 0

    def test_schema_validation_failure(self):
        """Test that schema validation failure in file is detected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = Path(tmpdir) / "report.json"
            invalid_report = {
                "valid_count": "not an int",
                "total_count": 100
            }
            with open(report_path, 'w') as f:
                json.dump(invalid_report, f)
            
            is_valid, errors = validate_report_file(report_path)
            assert is_valid is False
            assert any("wrong type" in err or "Missing" in err for err in errors)
