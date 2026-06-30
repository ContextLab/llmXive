"""
Tests for data hygiene utilities.
"""
import os
import tempfile
import json
from pathlib import Path
import pytest

from src.lib.data_hygiene import (
    compute_file_checksum,
    compute_directory_checksum,
    scan_text_for_pii,
    scan_file_for_pii,
    scan_directory_for_pii,
    validate_data_hygiene,
    generate_hygiene_report
)


class TestChecksumming:
    """Tests for checksum functionality."""
    
    def test_compute_file_checksum_sha256(self, tmp_path):
        """Test SHA256 checksum computation."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")
        
        checksum = compute_file_checksum(test_file)
        assert len(checksum) == 64  # SHA256 hex length
        assert all(c in '0123456789abcdef' for c in checksum)
        
    def test_compute_file_checksum_consistency(self, tmp_path):
        """Test that checksum is consistent across multiple calls."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content for consistency check")
        
        checksum1 = compute_file_checksum(test_file)
        checksum2 = compute_file_checksum(test_file)
        
        assert checksum1 == checksum2
        
    def test_compute_file_checksum_file_not_found(self):
        """Test error handling for non-existent file."""
        with pytest.raises(FileNotFoundError):
            compute_file_checksum(Path("/nonexistent/file.txt"))
            
    def test_compute_directory_checksum(self, tmp_path):
        """Test directory checksum computation."""
        # Create test files
        (tmp_path / "file1.txt").write_text("Content 1")
        (tmp_path / "subdir").mkdir()
        (tmp_path / "subdir" / "file2.txt").write_text("Content 2")
        
        checksums = compute_directory_checksum(tmp_path)
        
        assert "file1.txt" in checksums
        assert "subdir/file2.txt" in checksums
        assert len(checksums) == 2


class TestPIIScanning:
    """Tests for PII scanning functionality."""
    
    def test_detect_email(self):
        """Test email detection."""
        text = "Contact us at support@transitlm.org for help"
        findings = scan_text_for_pii(text)
        
        assert len(findings) >= 1
        assert any(f['type'] == 'email' for f in findings)
        
    def test_detect_phone(self):
        """Test phone number detection."""
        text = "Call us at 555-123-4567 or +1-555-987-6543"
        findings = scan_text_for_pii(text)
        
        assert len(findings) >= 1
        assert any(f['type'] == 'phone_us' for f in findings)
        
    def test_detect_ssn(self):
        """Test SSN detection."""
        text = "SSN: 123-45-6789"
        findings = scan_text_for_pii(text)
        
        assert len(findings) >= 1
        assert any(f['type'] == 'ssn' for f in findings)
        
    def test_safe_transit_data(self):
        """Test that safe transit data is not flagged."""
        text = "Route L from 34ST to FULTON, stop ID 123ABC"
        findings = scan_text_for_pii(text)
        
        # Should not flag station IDs or route IDs
        assert len(findings) == 0
        
    def test_no_pii_in_clean_text(self):
        """Test that clean text produces no findings."""
        text = "Take the L train from 34th Street to 1st Avenue"
        findings = scan_text_for_pii(text)
        
        assert len(findings) == 0
        
    def test_scan_file_with_pii(self, tmp_path):
        """Test file scanning with PII content."""
        test_file = tmp_path / "leak.txt"
        test_file.write_text("Email: user@example.com\nPhone: 555-123-4567")
        
        findings = scan_file_for_pii(test_file)
        
        assert len(findings) >= 2
        
    def test_scan_directory(self, tmp_path):
        """Test directory scanning."""
        # Create files with and without PII
        (tmp_path / "clean.txt").write_text("Safe content")
        (tmp_path / "leak.txt").write_text("Email: test@example.com")
        
        findings = scan_directory_for_pii(tmp_path)
        
        assert "clean.txt" not in findings
        assert "leak.txt" in findings


class TestDataHygieneValidation:
    """Tests for complete data hygiene validation."""
    
    def test_validate_clean_directory(self, tmp_path):
        """Test validation of a clean directory."""
        (tmp_path / "clean.txt").write_text("Safe transit data: Route L from 34ST")
        
        is_valid, report = validate_data_hygiene(tmp_path)
        
        assert is_valid
        assert report['summary']['total_files'] == 1
        assert report['summary']['files_with_findings'] == 0
        
    def test_validate_directory_with_pii(self, tmp_path):
        """Test validation of a directory with PII."""
        (tmp_path / "leak.txt").write_text("Contact: user@example.com")
        
        is_valid, report = validate_data_hygiene(tmp_path)
        
        # In non-strict mode, this might pass if no critical PII
        assert report['summary']['total_findings'] >= 1
        
    def test_generate_hygiene_report(self, tmp_path):
        """Test hygiene report generation."""
        (tmp_path / "test.txt").write_text("Safe data")
        
        report_path = generate_hygiene_report(tmp_path)
        
        assert report_path.exists()
        
        with open(report_path) as f:
            report = json.load(f)
            
        assert 'checksums' in report
        assert 'pii_findings' in report
        assert 'summary' in report
        assert 'validation_passed' in report