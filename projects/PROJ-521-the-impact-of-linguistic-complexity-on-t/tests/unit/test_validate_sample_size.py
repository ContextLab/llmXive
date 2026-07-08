"""
Unit tests for code/validate_sample_size.py (T022).
"""

import os
import sys
import csv
import json
import tempfile
from pathlib import Path
import pytest

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from validate_sample_size import (
    load_cleaned_responses_count,
    save_validation_report,
    main
)


class TestLoadCleanedResponsesCount:
    def test_count_rows(self, tmp_path):
        """Test that the function correctly counts rows in a CSV."""
        csv_file = tmp_path / "test.csv"
        # Create a CSV with header and 5 data rows
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["participant_id", "trust_rating"]) # Header
            for i in range(5):
                writer.writerow([f"p{i}", 3])

        count = load_cleaned_responses_count(csv_file)
        assert count == 5

    def test_count_empty_file(self, tmp_path):
        """Test that the function returns 0 for a file with only a header."""
        csv_file = tmp_path / "empty.csv"
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["participant_id", "trust_rating"])

        count = load_cleaned_responses_count(csv_file)
        assert count == 0

    def test_count_missing_file(self, tmp_path):
        """Test that the function returns 0 for a missing file."""
        missing_file = tmp_path / "nonexistent.csv"
        count = load_cleaned_responses_count(missing_file)
        assert count == 0


class TestSaveValidationReport:
    def test_save_report(self, tmp_path):
        """Test that the function saves a valid JSON report."""
        report_file = tmp_path / "report.json"
        save_validation_report(150, 100, "PASS", report_file)

        assert report_file.exists()
        with open(report_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        assert data["current_n"] == 150
        assert data["threshold"] == 100
        assert data["status"] == "PASS"
        assert data["message"] == "PASS"

    def test_save_report_fail(self, tmp_path):
        """Test that the function saves a valid JSON report for failure."""
        report_file = tmp_path / "report_fail.json"
        save_validation_report(50, 100, "FAIL", report_file)

        with open(report_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        assert data["current_n"] == 50
        assert data["status"] == "FAIL"
        assert data["message"] == "FAIL"