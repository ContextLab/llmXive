"""
Unit tests for Post-Hoc Duplicate Detection (T022h).

Tests the dedup.py module to ensure:
1. Duplicates are correctly identified
2. First occurrence is kept
3. Report is generated correctly
4. Edge cases are handled (empty data, no duplicates)
"""
import os
import sys
import csv
import tempfile
import json
from datetime import datetime
from pathlib import Path
import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.dedup import (
    load_submissions_data,
    detect_duplicates,
    write_dedup_report,
    run_deduplication
)


class TestLoadSubmissionsData:
    def test_load_valid_csv(self, tmp_path):
        """Test loading a valid CSV file."""
        csv_path = tmp_path / "test.csv"
        csv_path.write_text(
            "participant_id,timestamp,age\n"
            "uuid-1,2024-01-01T10:00:00,25\n"
            "uuid-2,2024-01-01T11:00:00,30\n"
        )

        data = load_submissions_data(str(csv_path))
        assert len(data) == 2
        assert data[0]['participant_id'] == 'uuid-1'
        assert data[1]['participant_id'] == 'uuid-2'

    def test_file_not_found(self, tmp_path):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            load_submissions_data(str(tmp_path / "nonexistent.csv"))

    def test_empty_file(self, tmp_path):
        """Test handling of empty CSV with headers."""
        csv_path = tmp_path / "empty.csv"
        csv_path.write_text("participant_id,timestamp,age\n")

        data = load_submissions_data(str(csv_path))
        assert len(data) == 0

    def test_no_headers(self, tmp_path):
        """Test that ValueError is raised for malformed CSV."""
        csv_path = tmp_path / "malformed.csv"
        csv_path.write_text("")

        with pytest.raises(ValueError):
            load_submissions_data(str(csv_path))


class TestDetectDuplicates:
    def test_no_duplicates(self):
        """Test data with no duplicates."""
        data = [
            {'participant_id': 'uuid-1', 'timestamp': '2024-01-01T10:00:00'},
            {'participant_id': 'uuid-2', 'timestamp': '2024-01-01T11:00:00'},
            {'participant_id': 'uuid-3', 'timestamp': '2024-01-01T12:00:00'},
        ]

        cleaned, duplicates = detect_duplicates(data)
        assert len(cleaned) == 3
        assert len(duplicates) == 0

    def test_with_duplicates(self):
        """Test data with duplicate participant_ids."""
        data = [
            {'participant_id': 'uuid-1', 'timestamp': '2024-01-01T10:00:00'},
            {'participant_id': 'uuid-2', 'timestamp': '2024-01-01T11:00:00'},
            {'participant_id': 'uuid-1', 'timestamp': '2024-01-01T12:00:00'},  # Duplicate
            {'participant_id': 'uuid-3', 'timestamp': '2024-01-01T13:00:00'},
            {'participant_id': 'uuid-1', 'timestamp': '2024-01-01T14:00:00'},  # Duplicate
        ]

        cleaned, duplicates = detect_duplicates(data)
        assert len(cleaned) == 3  # uuid-1, uuid-2, uuid-3
        assert len(duplicates) == 2  # Two duplicates of uuid-1

        # Verify first occurrence is kept
        assert cleaned[0]['participant_id'] == 'uuid-1'
        assert cleaned[0]['timestamp'] == '2024-01-01T10:00:00'

    def test_empty_data(self):
        """Test with empty input."""
        cleaned, duplicates = detect_duplicates([])
        assert len(cleaned) == 0
        assert len(duplicates) == 0

    def test_timestamp_ordering(self):
        """Test that first occurrence is determined by timestamp."""
        data = [
            {'participant_id': 'uuid-1', 'timestamp': '2024-01-01T12:00:00'},  # Later
            {'participant_id': 'uuid-1', 'timestamp': '2024-01-01T10:00:00'},  # Earlier (should be kept)
            {'participant_id': 'uuid-1', 'timestamp': '2024-01-01T11:00:00'},  # Middle
        ]

        cleaned, duplicates = detect_duplicates(data)
        assert len(cleaned) == 1
        assert len(duplicates) == 2

        # The earliest timestamp should be kept
        assert cleaned[0]['timestamp'] == '2024-01-01T10:00:00'

    def test_missing_participant_id(self):
        """Test handling of rows without participant_id."""
        data = [
            {'participant_id': '', 'timestamp': '2024-01-01T10:00:00'},
            {'participant_id': '', 'timestamp': '2024-01-01T11:00:00'},
            {'participant_id': 'uuid-1', 'timestamp': '2024-01-01T12:00:00'},
        ]

        cleaned, duplicates = detect_duplicates(data)
        # Empty IDs are kept but not treated as duplicates of each other
        assert len(cleaned) == 3
        assert len(duplicates) == 0


class TestWriteDedupReport:
    def test_write_with_duplicates(self, tmp_path):
        """Test report generation with duplicates."""
        output_path = tmp_path / "report.csv"
        duplicates = [
            {'participant_id': 'uuid-1', 'timestamp': '2024-01-01T12:00:00', 'hashed_ip': 'hash1'},
            {'participant_id': 'uuid-1', 'timestamp': '2024-01-01T14:00:00', 'hashed_ip': 'hash1'},
        ]

        write_dedup_report(duplicates, str(output_path))

        assert output_path.exists()

        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 2
        assert rows[0]['duplicate_index'] == '1'
        assert rows[0]['participant_id'] == 'uuid-1'

    def test_write_empty_report(self, tmp_path):
        """Test report generation with no duplicates."""
        output_path = tmp_path / "report.csv"

        write_dedup_report([], str(output_path))

        assert output_path.exists()

        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # Should have headers but no data rows
        assert len(rows) == 0


class TestRunDeduplication:
    def test_full_pipeline(self, tmp_path):
        """Test the complete deduplication pipeline."""
        # Create input file
        input_path = tmp_path / "submissions.csv"
        input_path.write_text(
            "participant_id,timestamp,age,hashed_ip\n"
            "uuid-1,2024-01-01T10:00:00,25,hash1\n"
            "uuid-2,2024-01-01T11:00:00,30,hash2\n"
            "uuid-1,2024-01-01T12:00:00,25,hash1\n"  # Duplicate
            "uuid-3,2024-01-01T13:00:00,35,hash3\n"
        )

        output_path = tmp_path / "dedup_report.csv"

        result = run_deduplication(
            input_path=str(input_path),
            output_path=str(output_path)
        )

        assert result['total_records'] == 4
        assert result['unique_records'] == 3
        assert result['duplicates_removed'] == 1
        assert os.path.exists(result['report_path'])

    def test_no_duplicates_found(self, tmp_path):
        """Test pipeline when no duplicates exist."""
        input_path = tmp_path / "submissions.csv"
        input_path.write_text(
            "participant_id,timestamp,age\n"
            "uuid-1,2024-01-01T10:00:00,25\n"
            "uuid-2,2024-01-01T11:00:00,30\n"
        )

        output_path = tmp_path / "dedup_report.csv"

        result = run_deduplication(
            input_path=str(input_path),
            output_path=str(output_path)
        )

        assert result['duplicates_removed'] == 0
        assert result['unique_records'] == 2

    def test_file_not_found(self, tmp_path):
        """Test that FileNotFoundError is raised for missing input."""
        with pytest.raises(FileNotFoundError):
            run_deduplication(input_path=str(tmp_path / "nonexistent.csv"))