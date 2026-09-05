import pytest
import json
import os
from pathlib import Path
import pandas as pd
from unittest.mock import patch, MagicMock

# Import the module under test
import sys
sys.path.insert(0, 'code')
from pipeline_validator import (
    check_file_exists,
    validate_json_structure,
    validate_csv_structure,
    run_integrity_checks,
    generate_final_report
)

class TestPipelineValidator:

    def test_check_file_exists_found(self, tmp_path):
        """Test file existence check when file exists."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        exists, reason = check_file_exists(str(test_file))
        assert exists is True
        assert reason is None

    def test_check_file_exists_not_found(self, tmp_path):
        """Test file existence check when file is missing."""
        missing_file = tmp_path / "nonexistent.txt"
        exists, reason = check_file_exists(str(missing_file))
        assert exists is False
        assert "does not exist" in reason

    def test_check_file_exists_empty(self, tmp_path):
        """Test file existence check when file is empty."""
        empty_file = tmp_path / "empty.txt"
        empty_file.write_text("")
        exists, reason = check_file_exists(str(empty_file))
        assert exists is False
        assert "empty" in reason

    def test_validate_json_structure_valid(self, tmp_path):
        """Test JSON validation with valid data."""
        test_file = tmp_path / "valid.json"
        test_file.write_text('{"key1": "value1", "key2": 123}')
        valid, reason = validate_json_structure(str(test_file), ["key1", "key2"])
        assert valid is True
        assert reason is None

    def test_validate_json_structure_missing_keys(self, tmp_path):
        """Test JSON validation with missing keys."""
        test_file = tmp_path / "missing.json"
        test_file.write_text('{"key1": "value1"}')
        valid, reason = validate_json_structure(str(test_file), ["key1", "key2"])
        assert valid is False
        assert "Missing keys" in reason

    def test_validate_json_structure_invalid_json(self, tmp_path):
        """Test JSON validation with invalid JSON."""
        test_file = tmp_path / "invalid.json"
        test_file.write_text('{invalid json}')
        valid, reason = validate_json_structure(str(test_file), ["key1"])
        assert valid is False
        assert "Invalid JSON" in reason

    def test_validate_csv_structure_valid(self, tmp_path):
        """Test CSV validation with valid data."""
        test_file = tmp_path / "valid.csv"
        df = pd.DataFrame({"col1": [1, 2], "col2": ["a", "b"]})
        df.to_csv(test_file, index=False)
        valid, reason = validate_csv_structure(str(test_file), ["col1", "col2"])
        assert valid is True
        assert reason is None

    def test_validate_csv_structure_empty(self, tmp_path):
        """Test CSV validation with empty data."""
        test_file = tmp_path / "empty.csv"
        df = pd.DataFrame({"col1": [], "col2": []})
        df.to_csv(test_file, index=False)
        valid, reason = validate_csv_structure(str(test_file), ["col1"])
        assert valid is False
        assert "no data rows" in reason.lower()

    def test_validate_csv_structure_missing_columns(self, tmp_path):
        """Test CSV validation with missing columns."""
        test_file = tmp_path / "missing.csv"
        df = pd.DataFrame({"col1": [1, 2]})
        df.to_csv(test_file, index=False)
        valid, reason = validate_csv_structure(str(test_file), ["col1", "col2"])
        assert valid is False
        assert "Missing columns" in reason

    def test_generate_final_report_success(self):
        """Test final report generation on success."""
        mock_results = {
            "timestamp": "2023-01-01T00:00:00",
            "checks": [{"status": "PASS"}],
            "summary": {"total_checks": 1, "passed": 1, "failed": 0, "warnings": 0}
        }
        report = generate_final_report(mock_results)
        assert report["pipeline_validation_report"]["status"] == "VALID"
        assert report["pipeline_validation_report"]["summary"]["passed"] == 1
        assert report["pipeline_validation_report"]["summary"]["failed"] == 0

    def test_generate_final_report_failure(self):
        """Test final report generation on failure."""
        mock_results = {
            "timestamp": "2023-01-01T00:00:00",
            "checks": [{"status": "FAIL"}],
            "summary": {"total_checks": 1, "passed": 0, "failed": 1, "warnings": 0}
        }
        report = generate_final_report(mock_results)
        assert report["pipeline_validation_report"]["status"] == "INVALID"
        assert report["pipeline_validation_report"]["summary"]["failed"] == 1