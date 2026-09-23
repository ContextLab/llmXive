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
    validate_and_record,
    get_project_root,
)


@pytest.fixture
def temp_csv_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
        f.write("id\tname\tvalue\n")
        f.write("1\tJohn Doe\t100\n")
        f.write("2\tJane Smith\t200\n")
        temp_path = f.name
    yield Path(temp_path)
    os.unlink(temp_path)


@pytest.fixture
def temp_pii_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
        f.write("id\temail\tvalue\n")
        f.write("1\tjohn.doe@example.com\t100\n")
        temp_path = f.name
    yield Path(temp_path)
    os.unlink(temp_path)


@pytest.fixture
def temp_state_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_calculate_file_checksum(temp_csv_file):
    checksum = calculate_file_checksum(temp_csv_file)
    assert isinstance(checksum, str)
    assert len(checksum) == 64  # SHA256 hex length


def test_scan_for_pii_no_pii():
    text = "This is a normal sentence with no PII."
    matches = scan_for_pii(text)
    assert matches == []


def test_scan_for_pii_exact_match():
    text = "Contact me at test@example.com"
    matches = scan_for_pii(text)
    emails = [m for m in matches if m["type"] == "email"]
    assert len(emails) == 1
    assert emails[0]["match"] == "test@example.com"


def test_scan_for_pii_regex_match():
    text = "My SSN is 123-45-6789"
    matches = scan_for_pii(text)
    ssns = [m for m in matches if m["type"] == "ssn"]
    assert len(ssns) == 1
    assert ssns[0]["match"] == "123-45-6789"


def test_validate_no_pii_pass(temp_csv_file):
    df = pd.read_csv(temp_csv_file, sep="\t")
    report = validate_no_pii(df)
    assert report["passed"] is True
    assert len(report["violations"]) == 0


def test_validate_no_pii_fail(temp_pii_file):
    df = pd.read_csv(temp_pii_file, sep="\t")
    report = validate_no_pii(df)
    assert report["passed"] is False
    assert len(report["violations"]) > 0
    assert report["violations"][0]["column"] == "email"


def test_record_checksums_creates_file(temp_csv_file, temp_state_dir):
    state_file = temp_state_dir / "test_hashes.json"
    checksums = record_checksums([temp_csv_file], state_file)

    assert len(checksums) == 1
    assert state_file.exists()

    with open(state_file, "r") as f:
        data = json.load(f)

    assert len(data) == 1
    assert temp_csv_file.name in data


def test_record_checksums_updates_existing(temp_csv_file, temp_state_dir):
    state_file = temp_state_dir / "test_hashes.json"
    # Initial write
    record_checksums([temp_csv_file], state_file)

    # Create a second file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f2:
        f2.write("col1\nval1\n")
        temp_csv2 = Path(f2.name)

    try:
        # Update with second file
        record_checksums([temp_csv2], state_file)

        with open(state_file, "r") as f:
            data = json.load(f)

        assert len(data) == 2
        assert temp_csv2.name in data
    finally:
        os.unlink(temp_csv2)


def test_validate_and_record_integration(temp_csv_file, temp_state_dir):
    state_file = temp_state_dir / "state.json"
    result = validate_and_record(temp_csv_file, state_file)

    assert result is True
    assert state_file.exists()


def test_validate_and_record_fails_on_pii(temp_pii_file, temp_state_dir):
    state_file = temp_state_dir / "state.json"
    result = validate_and_record(temp_pii_file, state_file)

    assert result is False
    # State file should not be updated if validation fails
    # (Implementation detail: current code returns False before recording if PII found)
    # But let's check the logic: validate_and_record checks PII first.
    # If PII found, it returns False immediately.
    # So state file might not exist or be empty if logic is strict.
    # In current implementation: returns False before record_checksums.
    # So state_file should not exist.
    assert not state_file.exists()