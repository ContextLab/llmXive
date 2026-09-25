"""
Unit tests for the PII Scanner module.
"""

import json
import os
import tempfile
from pathlib import Path

import pytest

from src.ingestion.pii_scanner import (
    calculate_file_checksum,
    scan_for_pii,
    validate_no_pii,
    run_pii_scan_and_checksums,
    PII_PATTERNS
)


@pytest.fixture
def temp_pii_file():
    """Create a temporary file with some PII content."""
    content = """
    Name: John Doe
    Email: john.doe@example.com
    Phone: 555-123-4567
    SSN: 123-45-6789
    Normal text without PII.
    """
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write(content)
        yield Path(f.name)
    os.unlink(f.name)


@pytest.fixture
def temp_clean_file():
    """Create a temporary file without PII."""
    content = """
    Sample ID: 12345
    Cohort: AGP
    Fiber intake: 25.5 g/day
    Read count: 15000
    """
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write(content)
        yield Path(f.name)
    os.unlink(f.name)


@pytest.fixture
def temp_missing_file():
    """Path to a non-existent file."""
    return Path("/tmp/non_existent_file_xyz_12345.txt")


def test_calculate_file_checksum(temp_pii_file):
    """Test SHA256 checksum calculation."""
    checksum = calculate_file_checksum(temp_pii_file)
    assert len(checksum) == 64  # SHA256 hex length
    assert all(c in '0123456789abcdef' for c in checksum)

    # Verify determinism
    checksum2 = calculate_file_checksum(temp_pii_file)
    assert checksum == checksum2


def test_calculate_file_checksum_missing(temp_missing_file):
    """Test checksum calculation on missing file raises error."""
    with pytest.raises(FileNotFoundError):
        calculate_file_checksum(temp_missing_file)


def test_scan_for_pii_detects_email(temp_pii_file):
    """Test PII scanner detects email addresses."""
    findings = scan_for_pii(temp_pii_file)
    assert "email" in findings
    assert len(findings["email"]) > 0
    assert "john.doe@example.com" in findings["email"][0]


def test_scan_for_pii_detects_phone(temp_pii_file):
    """Test PII scanner detects phone numbers."""
    findings = scan_for_pii(temp_pii_file)
    assert "phone" in findings
    assert len(findings["phone"]) > 0


def test_scan_for_pii_detects_ssn(temp_pii_file):
    """Test PII scanner detects SSN."""
    findings = scan_for_pii(temp_pii_file)
    assert "ssn" in findings
    assert len(findings["ssn"]) > 0


def test_scan_for_pii_clean_file(temp_clean_file):
    """Test PII scanner returns empty results for clean file."""
    findings = scan_for_pii(temp_clean_file)
    assert len(findings) == 0


def test_scan_for_pii_missing_file(temp_missing_file):
    """Test PII scanner raises error for missing file."""
    with pytest.raises(FileNotFoundError):
        scan_for_pii(temp_missing_file)


def test_validate_no_pii_empty_findings():
    """Test validation passes when no PII found."""
    findings = {}
    assert validate_no_pii(findings) is True


def test_validate_no_pii_with_findings():
    """Test validation fails when PII found."""
    findings = {
        "email": ["Line 1: test@example.com"],
        "phone": ["Line 2: 555-123-4567"]
    }
    assert validate_no_pii(findings) is False


def test_run_pii_scan_and_checksums(tmp_path):
    """Test full PII scan and checksum pipeline."""
    # Create test files
    pii_file = tmp_path / "pii_test.txt"
    pii_file.write_text("Email: test@example.com\n")

    clean_file = tmp_path / "clean_test.txt"
    clean_file.write_text("No PII here.\n")

    report_path = tmp_path / "report.json"
    checksum_path = tmp_path / "checksums.json"

    report, checksums = run_pii_scan_and_checksums(
        input_files=[pii_file, clean_file],
        output_report_path=report_path,
        output_checksums_path=checksum_path
    )

    # Verify report structure
    assert "files_scanned" in report
    assert "total_pii_matches" in report
    assert "pii_found" in report
    assert report["pii_found"] > 0  # PII should be detected

    # Verify checksums
    assert len(checksums) == 2
    assert "pii_test.txt" in str(checksums.keys())
    assert "clean_test.txt" in str(checksums.keys())

    # Verify files were written
    assert report_path.exists()
    assert checksum_path.exists()

    # Verify JSON content
    with open(report_path, 'r') as f:
        loaded_report = json.load(f)
    assert loaded_report["pii_found"] > 0

    with open(checksum_path, 'r') as f:
        loaded_checksums = json.load(f)
    assert len(loaded_checksums) == 2


def test_run_pii_scan_and_checksums_no_pii(tmp_path):
    """Test full pipeline when no PII is present."""
    clean_file = tmp_path / "clean_test.txt"
    clean_file.write_text("Sample data without PII.\n")

    report_path = tmp_path / "report.json"
    checksum_path = tmp_path / "checksums.json"

    report, checksums = run_pii_scan_and_checksums(
        input_files=[clean_file],
        output_report_path=report_path,
        output_checksums_path=checksum_path
    )

    assert report["pii_found"] == 0
    assert validate_no_pii(report["pii_by_type"]) is True