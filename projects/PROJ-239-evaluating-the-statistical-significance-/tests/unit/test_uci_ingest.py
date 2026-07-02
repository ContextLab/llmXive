"""
Unit tests for UCI data ingestion logic.
Since the actual download requires network access and large files,
these tests focus on the helper functions (checksum, PII scan)
and ensure the script structure is valid.
"""
import os
import tempfile
import hashlib
from pathlib import Path

import pytest
import pandas as pd

# Import the functions we want to test
# We assume the script is in code/uci_ingest.py
# We need to import from the parent directory or adjust sys.path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / 'code'))

from uci_ingest import compute_sha256, scan_pii, PII_REGEX_EMAIL

def test_compute_sha256():
    """Test that SHA-256 is computed correctly."""
    with tempfile.NamedTemporaryFile(delete=False, mode='w') as f:
        f.write("test data")
        temp_path = f.name

    try:
        # Known hash for "test data"
        expected = hashlib.sha256(b"test data").hexdigest()
        result = compute_sha256(temp_path)
        assert result == expected
    finally:
        os.unlink(temp_path)

def test_scan_pii_email_detection():
    """Test that the PII scanner detects email patterns."""
    with tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.csv') as f:
        f.write("id,email\n1,test@example.com\n2,noemail\n3,another@test.org\n")
        temp_path = f.name

    try:
        results = scan_pii(temp_path)
        assert len(results) > 0
        # Check that at least one email is found
        assert any("test@example.com" in r or "another@test.org" in r for r in results)
    finally:
        os.unlink(temp_path)

def test_scan_pii_no_email():
    """Test that the PII scanner returns empty list for no emails."""
    with tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.csv') as f:
        f.write("id,name\n1,John Doe\n2,Jane Smith\n")
        temp_path = f.name

    try:
        results = scan_pii(temp_path)
        assert len(results) == 0
    finally:
        os.unlink(temp_path)

def test_pii_regex():
    """Test the regex pattern directly."""
    assert PII_REGEX_EMAIL.match("user@domain.com")
    assert PII_REGEX_EMAIL.match("user.name+tag@sub.domain.co.uk")
    assert not PII_REGEX_EMAIL.match("not an email")
    assert not PII_REGEX_EMAIL.match("@missing.com")
    assert not PII_REGEX_EMAIL.match("missing@")