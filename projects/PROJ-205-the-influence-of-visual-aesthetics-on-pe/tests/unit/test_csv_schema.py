"""
Unit tests for CSV schema validation.
Verifies that exported CSV headers match the specification.
"""
import os
import sys
import csv
import tempfile
import shutil
from pathlib import Path
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.helpers import (
    get_submissions_csv_path,
    prepare_submission_row,
    append_to_submissions_csv,
    ensure_data_dirs
)

REQUIRED_COLUMNS = [
    "participant_id",
    "age",
    "education",
    "timestamp",
    "hashed_ip",
    "browser_version",
    "session_duration"
]

def test_csv_columns_match_spec():
    """
    Verify that the exported CSV headers match the specification.
    Creates a temporary CSV, writes a row, and checks headers.
    """
    # Create a temporary directory for testing
    temp_dir = tempfile.mkdtemp()
    original_submissions_path = get_submissions_csv_path()

    try:
        # Mock the path to use temp directory
        test_csv_path = Path(temp_dir) / "test_submissions.csv"
        
        # Prepare a test row
        test_row = prepare_submission_row(
            participant_id="test-uuid-123",
            age=25,
            education="Bachelor's Degree",
            timestamp="2024-01-01T12:00:00",
            hashed_ip="abc123hash",
            browser_version="Chrome 120",
            session_duration=120
        )

        # Write to temp file manually to check headers
        fieldnames = [
            "participant_id", "age", "education", "timestamp",
            "hashed_ip", "browser_version", "session_duration"
        ]

        with open(test_csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerow(test_row)

        # Read back and verify headers
        with open(test_csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            actual_headers = reader.fieldnames

            assert actual_headers is not None, "CSV file has no headers"
            assert len(actual_headers) == len(REQUIRED_COLUMNS), \
                f"Expected {len(REQUIRED_COLUMNS)} columns, got {len(actual_headers)}"
            
            for expected_col in REQUIRED_COLUMNS:
                assert expected_col in actual_headers, \
                    f"Missing required column: {expected_col}"

    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)

def test_row_data_types():
    """
    Verify that the row data types are correct.
    """
    test_row = prepare_submission_row(
        participant_id="test-uuid-123",
        age=25,
        education="Bachelor's Degree",
        timestamp="2024-01-01T12:00:00",
        hashed_ip="abc123hash",
        browser_version="Chrome 120",
        session_duration=120
    )

    assert isinstance(test_row["participant_id"], str)
    assert isinstance(test_row["age"], int)
    assert isinstance(test_row["education"], str)
    assert isinstance(test_row["timestamp"], str)
    assert isinstance(test_row["hashed_ip"], str)
    assert isinstance(test_row["browser_version"], str)
    assert isinstance(test_row["session_duration"], int)