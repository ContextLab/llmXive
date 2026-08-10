"""
Unit tests for src.ingestion.validation module.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pandas as pd
import pytest

from src.ingestion.validation import (
    calculate_file_checksum,
    scan_for_pii,
    validate_no_pii,
    record_checksums,
    validate_and_record
)


@pytest.fixture
def temp_csv_file():
    """Create a temporary CSV file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("id,value\n1,100\n2,200\n")
        path = Path(f.name)
    yield path
    os.unlink(path)


@pytest.fixture
def temp_pii_file():
    """Create a temporary CSV file with PII columns."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("id,first_name,ssn\n1,John,123-45-6789\n2,Jane,987-65-4321\n")
        path = Path(f.name)
    yield path
    os.unlink(path)


@pytest.fixture
def temp_state_dir():
    """Create a temporary directory for state files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_calculate_file_checksum(temp_csv_file):
    """Test that checksum is calculated correctly and is deterministic."""
    checksum1 = calculate_file_checksum(temp_csv_file)
    checksum2 = calculate_file_checksum(temp_csv_file)
    assert checksum1 == checksum2
    assert len(checksum1) == 64  # SHA-256 hex length


def test_scan_for_pii_no_pii():
    """Test scan_for_pii on a clean dataframe."""
    df = pd.DataFrame({"id": [1, 2], "fiber_g": [10, 20], "age": [30, 40]})
    violations = scan_for_pii(df)
    assert len(violations) == 0


def test_scan_for_pii_exact_match():
    """Test scan_for_pii detects exact PII column matches."""
    df = pd.DataFrame({"id": [1], "first_name": ["John"], "value": [10]})
    violations = scan_for_pii(df)
    assert len(violations) == 1
    assert violations[0]["column"] == "first_name"
    assert "Exact match" in violations[0]["reason"]


def test_scan_for_pii_regex_match():
    """Test scan_for_pii detects regex PII patterns."""
    df = pd.DataFrame({"id": [1], "social_security_number": ["123"], "value": [10]})
    violations = scan_for_pii(df)
    assert len(violations) >= 1
    assert any("Regex match" in v["reason"] or "Exact match" in v["reason"] for v in violations)


def test_validate_no_pii_pass():
    """Test validate_no_pii returns True for clean data."""
    df = pd.DataFrame({"id": [1, 2], "fiber": [10, 20]})
    assert validate_no_pii(df) is True


def test_validate_no_pii_fail():
    """Test validate_no_pii returns False for data with PII."""
    df = pd.DataFrame({"id": [1], "ssn": ["123-45-6789"]})
    assert validate_no_pii(df) is False


def test_record_checksums_creates_file(temp_state_dir, temp_csv_file):
    """Test that record_checksums creates the state file with correct content."""
    state_file = temp_state_dir / "checksums.json"
    result = record_checksums([temp_csv_file], state_file)

    assert state_file.exists()
    assert len(result) == 1

    with open(state_file, 'r') as f:
        data = json.load(f)

    # Check that the relative path is used
    assert any(temp_csv_file.name in k for k in data.keys())
    assert all(len(v) == 64 for v in data.values())


def test_validate_and_record_integration(temp_csv_file, temp_state_dir):
    """Test the full validation and recording pipeline."""
    output_path = temp_csv_file
    input_path = temp_csv_file
    state_file = temp_state_dir / "checksums.json"

    # Create a clean DataFrame to write
    df = pd.DataFrame({"id": [1, 2], "fiber": [10, 20]})
    df.to_csv(output_path, index=False)

    success = validate_and_record(input_path, output_path, state_file)

    assert success is True
    assert state_file.exists()


def test_validate_and_record_fails_on_pii(temp_pii_file, temp_state_dir):
    """Test that validation fails when PII is detected."""
    output_path = temp_pii_file
    input_path = temp_pii_file
    state_file = temp_state_dir / "checksums.json"

    success = validate_and_record(input_path, output_path, state_file)

    assert success is False
    # State file might not be updated if validation fails early
    # but the primary check is the return value