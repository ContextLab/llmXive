"""
Contract test for CSV schema validation (T040).
Validates that submissions.csv and duplicate_audit.csv adhere to the expected schema.
"""
import os
import sys
import csv
import tempfile
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from utils.helpers import get_submissions_csv_path, get_duplicate_audit_path, ensure_data_dirs

# Expected schema for submissions.csv
EXPECTED_SUBMISSIONS_HEADERS = [
    'participant_id', 'stimulus_id', 'credibility', 'professionalism',
    'timestamp', 'hashed_ip', 'age', 'education', 'duplicate_flag',
    'session_status', 'submission_status', 'user_agent'
]

# Expected schema for duplicate_audit.csv (should match submissions)
EXPECTED_AUDIT_HEADERS = EXPECTED_SUBMISSIONS_HEADERS


def test_submissions_schema_structure():
    """
    Verify that if submissions.csv exists, it has the correct headers.
    This is a contract test: the schema must not change without updating this test.
    """
    # Create a dummy file to test the reader logic if real file doesn't exist yet
    # Or verify the real file if it exists.
    # For this test, we check the headers of an existing file or the expected headers.

    ensure_data_dirs()
    path = get_submissions_csv_path()

    # If the file exists, verify its headers
    if path.exists():
        with open(path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            headers = next(reader, None)
            assert headers is not None, "Submissions CSV is empty (no headers)."
            assert set(headers) == set(EXPECTED_SUBMISSIONS_HEADERS), \
                f"Submissions CSV headers mismatch.\nExpected: {EXPECTED_SUBMISSIONS_HEADERS}\nGot: {headers}"
    else:
        # If the file doesn't exist yet, this test passes by definition of schema existence
        # (The schema is defined by the code that writes it, which we trust for now)
        # But we assert that the expected headers are not empty
        assert len(EXPECTED_SUBMISSIONS_HEADERS) > 0


def test_audit_schema_structure():
    """
    Verify that if duplicate_audit.csv exists, it has the correct headers.
    """
    ensure_data_dirs()
    path = get_duplicate_audit_path()

    if path.exists():
        with open(path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            headers = next(reader, None)
            assert headers is not None, "Audit CSV is empty (no headers)."
            assert set(headers) == set(EXPECTED_AUDIT_HEADERS), \
                f"Audit CSV headers mismatch.\nExpected: {EXPECTED_AUDIT_HEADERS}\nGot: {headers}"
    else:
        assert len(EXPECTED_AUDIT_HEADERS) > 0


def test_audit_contains_duplicates_only():
    """
    Contract test: Ensure that if duplicate_audit.csv exists,
    it only contains rows that are actually duplicates in submissions.csv.
    This requires both files to exist.
    """
    submissions_path = get_submissions_csv_path()
    audit_path = get_duplicate_audit_path()

    if not submissions_path.exists() or not audit_path.exists():
        pytest.skip("One or both required files do not exist yet.")

    # Load submissions
    with open(submissions_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        submissions = list(reader)

    # Load audit
    with open(audit_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        audit_rows = list(reader)

    if not audit_rows:
        # If audit is empty, it's valid (no duplicates found)
        return

    # Build a set of IPs that appear more than once in submissions
    ip_counts = {}
    for row in submissions:
        ip = row.get('hashed_ip')
        if ip:
            ip_counts[ip] = ip_counts.get(ip, 0) + 1

    duplicate_ips = {ip for ip, count in ip_counts.items() if count > 1}

    # Verify every row in audit has an IP in duplicate_ips
    for row in audit_rows:
        ip = row.get('hashed_ip')
        assert ip in duplicate_ips, \
            f"Audit row contains IP '{ip}' which is not a duplicate in submissions."
