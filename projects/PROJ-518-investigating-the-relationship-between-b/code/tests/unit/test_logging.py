"""
Unit tests for ``code.utils.logging.log_exclusion``.
The tests verify that:
1. The log file is created in the expected location.
2. The CSV header is written on the first call.
3. Subsequent calls append rows without duplicating the header.
4. Invalid reason codes raise a ``ValueError``.
"""

import csv
from pathlib import Path

import pytest

# Import the function under test.
from utils.logging import log_exclusion, REASON_CODES

# Resolve the log path using the same helper the implementation uses.
from llmxive_toolkit import paths

LOG_PATH = paths.data("interim", "data_exclusion_log.txt")

@pytest.fixture(autouse=True)
def clean_log_file():
    """Ensure a clean state before each test."""
    # Remove the log file if it exists.
    if LOG_PATH.is_file():
        LOG_PATH.unlink()
    yield
    # Clean up after the test as well.
    if LOG_PATH.is_file():
        LOG_PATH.unlink()

def read_log_rows():
    """Utility to read the CSV file and return a list of dict rows."""
    with LOG_PATH.open(newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)

def test_log_creation_and_header():
    """First call should create the file and write the header."""
    subject = "sub_test_001"
    reason = "MISSING_SCAN"
    assert reason in REASON_CODES

    # Call the function – this should create the file.
    log_exclusion(reason, subject)

    # Verify file existence.
    assert LOG_PATH.is_file(), "Log file was not created"

    # Verify header and single data row.
    rows = read_log_rows()
    assert len(rows) == 1
    row = rows[0]
    assert row["subject_id"] == subject
    assert row["reason"] == reason
    # Timestamp should be a non‑empty ISO string.
    assert row["timestamp"]

def test_log_appends_without_duplicate_header():
    """Subsequent calls should append rows, not rewrite the header."""
    subjects = ["sub_a", "sub_b", "sub_c"]
    reason = "HIGH_MOTION"

    for s in subjects:
        log_exclusion(reason, s)

    rows = read_log_rows()
    # Expect three data rows plus a single header (handled by DictReader).
    assert len(rows) == 3
    retrieved_subjects = [r["subject_id"] for r in rows]
    assert retrieved_subjects == subjects

def test_invalid_reason_raises():
    """Providing a non‑standard reason should raise ValueError."""
    with pytest.raises(ValueError):
        log_exclusion("UNKNOWN_REASON", "sub_x")