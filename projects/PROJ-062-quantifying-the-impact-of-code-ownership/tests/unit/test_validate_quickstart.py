"""
Unit tests for the quickstart validation script.
"""
import os
import json
import csv
import tempfile
from pathlib import Path
import pytest
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from validate_quickstart import (
    validate_json_structure,
    validate_csv_structure,
    validate_file_exists,
    run_validation
)

class TestValidateJsonStructure:
    def test_valid_json_with_all_required_keys(self, tmp_path):
        """Test validation of a properly structured JSON file."""
        file_path = tmp_path / "test.json"
        data = {
            "metadata": {
                "associational_framing": "This is an associational study.",
                "random_seed": 42,
                "timestamp": "2024-01-01"
            },
            "correlation_results": {},
            "vif_results": {},
            "sensitivity_analysis": {},
            "non_linearity_test": {}
        }
        with open(file_path, 'w') as f:
            json.dump(data, f)

        schema = {
            "required_keys": ["metadata", "correlation_results", "vif_results", "sensitivity_analysis", "non_linearity_test"],
            "metadata_required_keys": ["associational_framing", "random_seed", "timestamp"]
        }

        assert validate_json_structure(file_path, schema) is True

    def test_missing_required_key(self, tmp_path):
        """Test validation fails when a required key is missing."""
        file_path = tmp_path / "test.json"
        data = {
            "metadata": {},
            "correlation_results": {}
        }
        with open(file_path, 'w') as f:
            json.dump(data, f)

        schema = {
            "required_keys": ["metadata", "correlation_results", "vif_results"],
            "metadata_required_keys": []
        }

        assert validate_json_structure(file_path, schema) is False

    def test_invalid_json(self, tmp_path):
        """Test validation fails for invalid JSON."""
        file_path = tmp_path / "test.json"
        file_path.write_text("{ invalid json }")

        schema = {"required_keys": []}

        assert validate_json_structure(file_path, schema) is False

class TestValidateCsvStructure:
    def test_valid_csv_with_all_columns(self, tmp_path):
        """Test validation of a properly structured CSV file."""
        file_path = tmp_path / "test.csv"
        with open(file_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["cutoff", "count_significant", "count_total", "random_seed"])
            writer.writeheader()
            writer.writerow({"cutoff": 0.05, "count_significant": 5, "count_total": 10, "random_seed": 42})

        schema = {
            "required_columns": ["cutoff", "count_significant", "count_total", "random_seed"]
        }

        assert validate_csv_structure(file_path, schema) is True

    def test_missing_required_column(self, tmp_path):
        """Test validation fails when a required column is missing."""
        file_path = tmp_path / "test.csv"
        with open(file_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["cutoff", "count_significant"])
            writer.writeheader()
            writer.writerow({"cutoff": 0.05, "count_significant": 5})

        schema = {
            "required_columns": ["cutoff", "count_significant", "count_total"]
        }

        assert validate_csv_structure(file_path, schema) is False

    def test_empty_csv(self, tmp_path):
        """Test validation fails for empty CSV."""
        file_path = tmp_path / "test.csv"
        file_path.write_text("")

        schema = {
            "required_columns": ["cutoff"]
        }

        assert validate_csv_structure(file_path, schema) is False

class TestValidateFileExists:
    def test_file_exists(self, tmp_path):
        """Test validation passes when file exists."""
        file_path = tmp_path / "test.txt"
        file_path.write_text("content")

        assert validate_file_exists(file_path) is True

    def test_file_missing(self, tmp_path):
        """Test validation fails when file doesn't exist."""
        file_path = tmp_path / "nonexistent.txt"

        assert validate_file_exists(file_path) is False