import os
import json
import tempfile
import csv
from pathlib import Path
import pytest
import sys

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.quickstart_validation import (
    check_file_exists, 
    check_json_validity, 
    check_csv_validity,
    validate_artifacts
)

class TestFileChecks:
    def test_check_file_exists_found(self, tmp_path):
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        assert check_file_exists(str(test_file)) is True

    def test_check_file_exists_missing(self, tmp_path):
        assert check_file_exists(str(tmp_path / "missing.txt")) is False

    def test_check_json_validity_valid(self, tmp_path):
        test_file = tmp_path / "valid.json"
        test_file.write_text('{"key": "value"}')
        assert check_json_validity(str(test_file)) is True

    def test_check_json_validity_invalid(self, tmp_path):
        test_file = tmp_path / "invalid.json"
        test_file.write_text('{key: value}') # Invalid JSON
        assert check_json_validity(str(test_file)) is False

    def test_check_csv_validity_valid(self, tmp_path):
        test_file = tmp_path / "valid.csv"
        with open(test_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['col1', 'col2'])
            writer.writerow(['val1', 'val2'])
        assert check_csv_validity(str(test_file)) is True

    def test_check_csv_validity_missing(self, tmp_path):
        assert check_csv_validity(str(tmp_path / "missing.csv")) is False

class TestValidationLogic:
    def test_validate_artifacts_empty_dir(self, tmp_path):
        # Change to a temp directory with no expected artifacts
        # This should fail gracefully
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            # We expect this to return False because artifacts are missing
            result = validate_artifacts()
            assert result is False
        finally:
            os.chdir(original_cwd)