"""
Unit tests for the duplicate detection module (code/utils/dedup.py).
"""
import os
import sys
import csv
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import pytest

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.dedup import (
    load_submissions_data,
    detect_duplicates,
    write_dedup_report,
    run_deduplication
)
from utils.helpers import get_project_root

class TestLoadSubmissionsData:
    def test_load_valid_csv(self, tmp_path):
        """Test loading a valid CSV file."""
        csv_file = tmp_path / "test.csv"
        data = [
            {"participant_id": "1", "value": "A"},
            {"participant_id": "2", "value": "B"}
        ]
        with open(csv_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["participant_id", "value"])
            writer.writeheader()
            writer.writerows(data)

        result = load_submissions_data(str(csv_file))
        assert len(result) == 2
        assert result[0]["participant_id"] == "1"

    def test_load_missing_file(self, tmp_path):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            load_submissions_data(str(tmp_path / "nonexistent.csv"))

    def test_load_empty_file(self, tmp_path):
        """Test that ValueError is raised for empty file."""
        csv_file = tmp_path / "empty.csv"
        csv_file.write_text("")
        with pytest.raises(ValueError):
            load_submissions_data(str(csv_file))

class TestDetectDuplicates:
    def test_no_duplicates(self):
        """Test detection with no duplicates."""
        data = [
            {"participant_id": "1", "value": "A"},
            {"participant_id": "2", "value": "B"},
            {"participant_id": "3", "value": "C"}
        ]
        unique, dups = detect_duplicates(data)
        assert len(unique) == 3
        assert len(dups) == 0

    def test_with_duplicates(self):
        """Test detection with duplicates."""
        data = [
            {"participant_id": "1", "value": "A"},
            {"participant_id": "2", "value": "B"},
            {"participant_id": "1", "value": "A_dup"},
            {"participant_id": "3", "value": "C"},
            {"participant_id": "1", "value": "A_triple"}
        ]
        unique, dups = detect_duplicates(data)
        
        # First occurrence of '1' should be in unique
        assert len(unique) == 3 
        assert unique[0]["participant_id"] == "1"
        
        # Two duplicates of '1' should be in dups
        assert len(dups) == 2
        assert all(row["participant_id"] == "1" for row in dups)

    def test_missing_id_handling(self):
        """Test handling of rows with missing participant_id."""
        data = [
            {"participant_id": None, "value": "A"},
            {"participant_id": None, "value": "B"},
            {"participant_id": "1", "value": "C"}
        ]
        unique, dups = detect_duplicates(data)
        # None IDs are treated as unique (or skipped, but here they are kept as unique)
        # Based on implementation: if row_id is None, it goes to unique.
        # So 2 None rows + 1 "1" row = 3 unique.
        assert len(unique) == 3
        assert len(dups) == 0

class TestWriteDedupReport:
    def test_write_report_with_data(self, tmp_path):
        """Test writing a report with duplicate data."""
        dups = [
            {"participant_id": "1", "timestamp": "2023-01-01", "value": "X"},
            {"participant_id": "1", "timestamp": "2023-01-02", "value": "Y"}
        ]
        report_path = tmp_path / "report.csv"
        write_dedup_report(dups, str(report_path))

        assert report_path.exists()
        with open(report_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 2
            assert "detected_at" in reader.fieldnames
            assert all(row["participant_id"] == "1" for row in rows)

    def test_write_report_empty(self, tmp_path):
        """Test writing a report with no duplicates."""
        report_path = tmp_path / "report_empty.csv"
        write_dedup_report([], str(report_path))

        assert report_path.exists()
        with open(report_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 0
            # Check headers exist
            assert 'participant_id' in reader.fieldnames

class TestRunDeduplication:
    def test_full_pipeline(self, tmp_path):
        """Test the full deduplication pipeline."""
        input_data = [
            {"participant_id": "1", "age": 20},
            {"participant_id": "2", "age": 25},
            {"participant_id": "1", "age": 20}, # Duplicate
            {"participant_id": "3", "age": 30}
        ]
        
        input_file = tmp_path / "input.csv"
        report_file = tmp_path / "report.csv"
        cleaned_file = tmp_path / "cleaned.csv"

        with open(input_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["participant_id", "age"])
            writer.writeheader()
            writer.writerows(input_data)

        result = run_deduplication(
            input_path=str(input_file),
            output_report_path=str(report_file),
            keep_original_path=str(cleaned_file)
        )

        assert result["total_rows"] == 4
        assert result["unique_rows"] == 3
        assert result["duplicate_rows_removed"] == 1
        assert result["status"] == "success"
        assert report_file.exists()
        assert cleaned_file.exists()

        # Verify cleaned file content
        with open(cleaned_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 3
            ids = [r["participant_id"] for r in rows]
            assert ids.count("1") == 1

    def test_pipeline_no_duplicates(self, tmp_path):
        """Test pipeline when no duplicates exist."""
        input_data = [
            {"participant_id": "1", "age": 20},
            {"participant_id": "2", "age": 25}
        ]
        
        input_file = tmp_path / "input.csv"
        report_file = tmp_path / "report.csv"
        cleaned_file = tmp_path / "cleaned.csv"

        with open(input_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["participant_id", "age"])
            writer.writeheader()
            writer.writerows(input_data)

        result = run_deduplication(
            input_path=str(input_file),
            output_report_path=str(report_file),
            keep_original_path=str(cleaned_file)
        )

        assert result["duplicate_rows_removed"] == 0
        assert result["unique_rows"] == 2