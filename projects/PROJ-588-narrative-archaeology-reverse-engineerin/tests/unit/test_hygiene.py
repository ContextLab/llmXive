"""
Unit tests for data hygiene module.
"""
import os
import json
import tempfile
import shutil
from pathlib import Path
import pytest

from data.hygiene import (
    verify_raw_data_checksum,
    scan_for_pii,
    enforce_no_inplace_modifications,
    run_data_hygiene_check
)
from data.download import calculate_md5

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory with test files."""
    temp_dir = tempfile.mkdtemp()
    data_dir = Path(temp_dir)
    
    # Create test files
    (data_dir / "test.txt").write_text("Hello, world!\nContact: test@example.com\nPhone: 555-123-4567")
    (data_dir / "safe.txt").write_text("This file has no PII.")
    (data_dir / "data.csv").write_text("id,name,value\n1,Alice,100\n2,Bob,200")
    
    yield data_dir
    
    # Cleanup
    shutil.rmtree(temp_dir)

@pytest.fixture
def checksum_manifest(temp_data_dir):
    """Create a checksum manifest file."""
    manifest_path = temp_data_dir / "checksums.txt"
    with open(manifest_path, 'w') as f:
        for file_path in temp_data_dir.glob("*.txt"):
            md5 = calculate_md5(file_path)
            f.write(f"{md5}  {file_path.name}\n")
    return manifest_path

def test_verify_raw_data_checksum_valid(temp_data_dir, checksum_manifest):
    """Test checksum verification with valid files."""
    all_valid, failures = verify_raw_data_checksum(temp_data_dir, checksum_manifest)
    assert all_valid is True
    assert len(failures) == 0

def test_verify_raw_data_checksum_invalid(temp_data_dir, checksum_manifest):
    """Test checksum verification with corrupted file."""
    # Corrupt a file
    (temp_data_dir / "test.txt").write_text("Corrupted content")
    
    all_valid, failures = verify_raw_data_checksum(temp_data_dir, checksum_manifest)
    assert all_valid is False
    assert "test.txt" in failures

def test_verify_raw_data_checksum_missing_file(temp_data_dir, checksum_manifest):
    """Test checksum verification with missing file."""
    # Remove a file
    (temp_data_dir / "safe.txt").unlink()
    
    all_valid, failures = verify_raw_data_checksum(temp_data_dir, checksum_manifest)
    assert all_valid is False
    assert "safe.txt" in failures

def test_scan_for_pii_email(temp_data_dir):
    """Test PII scanning for email addresses."""
    findings = scan_for_pii(temp_data_dir / "test.txt")
    assert len(findings['email']) == 1
    assert "test@example.com" in findings['email']

def test_scan_for_pii_phone(temp_data_dir):
    """Test PII scanning for phone numbers."""
    findings = scan_for_pii(temp_data_dir / "test.txt")
    assert len(findings['phone_us']) == 1
    assert "555-123-4567" in findings['phone_us']

def test_scan_for_pii_safe_file(temp_data_dir):
    """Test PII scanning on file without PII."""
    findings = scan_for_pii(temp_data_dir / "safe.txt")
    assert all(len(v) == 0 for v in findings.values())

def test_enforce_no_inplace_modifications(temp_data_dir):
    """Test backup creation for file protection."""
    with tempfile.TemporaryDirectory() as backup_dir:
        backup_path = Path(backup_dir)
        result = enforce_no_inplace_modifications(temp_data_dir / "test.txt", backup_path)
        assert result is True
        assert (backup_path / "test.txt").exists()

def test_run_data_hygiene_check(temp_data_dir, checksum_manifest):
    """Test full hygiene check workflow."""
    with tempfile.TemporaryDirectory() as output_dir:
        output_path = Path(output_dir)
        results = run_data_hygiene_check(temp_data_dir, output_path, checksum_manifest)
        
        assert 'overall_status' in results
        assert 'checksum_verified' in results
        assert 'pii_findings' in results
        assert 'backups_created' in results
        
        # Check report was written
        report_path = output_path / "hygiene_report.json"
        assert report_path.exists()
        
        with open(report_path) as f:
            report = json.load(f)
            assert report == results
