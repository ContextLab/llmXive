"""
Unit tests for PII scanning functionality.
Tests the security_scan module for detecting various PII patterns.
"""
import os
import re
import tempfile
import pytest
from pathlib import Path
import sys
import csv
import json

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from security_scan import (
    is_valid_credit_card,
    scan_text_for_pii,
    scan_csv_file,
    scan_json_file,
    scan_yaml_file,
    scan_text_file,
    scan_directory,
    generate_report
)

class TestCreditCardValidation:
    """Tests for credit card validation using Luhn algorithm."""

    def test_valid_credit_card(self):
        """Test that valid credit card numbers pass validation."""
        # Test Visa card (4111111111111111 is a test number)
        assert is_valid_credit_card("4111111111111111") is True
        # Test with dashes
        assert is_valid_credit_card("4111-1111-1111-1111") is True
        # Test with spaces
        assert is_valid_credit_card("4111 1111 1111 1111") is True

    def test_invalid_credit_card(self):
        """Test that invalid credit card numbers fail validation."""
        # Invalid checksum
        assert is_valid_credit_card("4111111111111112") is False
        # Too short
        assert is_valid_credit_card("411111111111") is False
        # Too long
        assert is_valid_credit_card("41111111111111111111") is False
        # Non-numeric
        assert is_valid_credit_card("411111111111111a") is False

class TestTextScanning:
    """Tests for text-based PII scanning."""

    def test_email_detection(self):
        """Test detection of email addresses."""
        text = "Contact us at test@example.com or support@company.org"
        findings = scan_text_for_pii(text)
        email_findings = [f for f in findings if f['type'] == 'email']
        assert len(email_findings) == 2
        assert 'test@example.com' in [f['match'] for f in email_findings]
        assert 'support@company.org' in [f['match'] for f in email_findings]

    def test_ssn_detection(self):
        """Test detection of Social Security Numbers."""
        text = "SSN: 123-45-6789 or 987654321"
        findings = scan_text_for_pii(text)
        ssn_findings = [f for f in findings if f['type'] in ['ssn', 'ssn_compact']]
        assert len(ssn_findings) == 2

    def test_phone_detection(self):
        """Test detection of US phone numbers."""
        text = "Call (555) 123-4567 or 555-123-4567 or +1-555-123-4567"
        findings = scan_text_for_pii(text)
        phone_findings = [f for f in findings if f['type'] == 'phone_us']
        assert len(phone_findings) == 3

    def test_no_pii(self):
        """Test that text without PII returns empty findings."""
        text = "This is a normal sentence with no sensitive information."
        findings = scan_text_for_pii(text)
        # Should be empty or very few (maybe IP or URL if present)
        assert len(findings) == 0

class TestCSVScanning:
    """Tests for CSV file scanning."""

    def test_csv_with_pii(self):
        """Test scanning a CSV file containing PII."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(['name', 'email', 'ssn'])
            writer.writerow(['John Doe', 'john@example.com', '123-45-6789'])
            temp_path = Path(f.name)

        try:
            findings = scan_csv_file(temp_path)
            email_findings = [f for f in findings if f['type'] == 'email']
            ssn_findings = [f for f in findings if f['type'] in ['ssn', 'ssn_compact']]
            assert len(email_findings) == 1
            assert len(ssn_findings) == 1
        finally:
            temp_path.unlink()

    def test_csv_without_pii(self):
        """Test scanning a CSV file without PII."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(['name', 'age', 'city'])
            writer.writerow(['John Doe', '30', 'New York'])
            temp_path = Path(f.name)

        try:
            findings = scan_csv_file(temp_path)
            assert len(findings) == 0
        finally:
            temp_path.unlink()

class TestJSONScanning:
    """Tests for JSON file scanning."""

    def test_json_with_pii(self):
        """Test scanning a JSON file containing PII."""
        data = {
            "user": "john",
            "email": "john@example.com",
            "ssn": "123-45-6789"
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = Path(f.name)

        try:
            findings = scan_json_file(temp_path)
            email_findings = [f for f in findings if f['type'] == 'email']
            ssn_findings = [f for f in findings if f['type'] in ['ssn', 'ssn_compact']]
            assert len(email_findings) == 1
            assert len(ssn_findings) == 1
        finally:
            temp_path.unlink()

class TestDirectoryScanning:
    """Tests for directory scanning."""

    def test_directory_scan(self):
        """Test scanning a directory with multiple files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create a CSV file with PII
            csv_file = temp_path / "test.csv"
            with open(csv_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['email'])
                writer.writerow(['test@example.com'])
            
            # Create a text file with PII
            txt_file = temp_path / "test.txt"
            with open(txt_file, 'w') as f:
                f.write("Contact: support@company.org")
            
            # Create a subdirectory with a file
            subdir = temp_path / "subdir"
            subdir.mkdir()
            sub_file = subdir / "sub.txt"
            with open(sub_file, 'w') as f:
                f.write("Phone: (555) 123-4567")
            
            findings = scan_directory(temp_path)
            
            assert len(findings) == 3  # 1 email in csv, 1 email in txt, 1 phone in subdir
            types = [f['type'] for f in findings]
            assert types.count('email') == 2
            assert types.count('phone_us') == 1

    def test_empty_directory(self):
        """Test scanning an empty directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            findings = scan_directory(temp_path)
            assert len(findings) == 0

class TestReportGeneration:
    """Tests for report generation."""

    def test_report_generation(self):
        """Test that a report is generated correctly."""
        findings = [
            {
                'file': 'test.csv',
                'type': 'email',
                'match': 'test@example.com',
                'line_number': 2
            }
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "report.txt"
            generate_report(findings, output_path)
            
            assert output_path.exists()
            with open(output_path, 'r') as f:
                content = f.read()
                assert "PII SCAN REPORT" in content
                assert "test@example.com" in content
                assert "email" in content

    def test_report_no_findings(self):
        """Test report generation with no findings."""
        findings = []
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "report.txt"
            generate_report(findings, output_path)
            
            assert output_path.exists()
            with open(output_path, 'r') as f:
                content = f.read()
                assert "No PII detected" in content

class TestIntegration:
    """Integration tests for the full PII scan workflow."""

    def test_full_scan_workflow(self):
        """Test the complete workflow from scanning to reporting."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test data directory
            data_dir = temp_path / "data"
            data_dir.mkdir()
            (data_dir / "raw").mkdir()
            (data_dir / "processed").mkdir()
            
            # Create a file with PII
            test_file = data_dir / "raw" / "participants.csv"
            with open(test_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['id', 'email', 'phone'])
                writer.writerow(['1', 'user@test.com', '(555) 123-4567'])
            
            # Create a file without PII
            clean_file = data_dir / "processed" / "metrics.csv"
            with open(clean_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['id', 'value'])
                writer.writerow(['1', '0.5'])
            
            # Scan the data directory
            findings = scan_directory(data_dir)
            
            # Should find email and phone
            assert len(findings) == 2
            
            # Generate report
            report_path = temp_path / "pii_scan_report.txt"
            generate_report(findings, report_path)
            
            assert report_path.exists()
            with open(report_path, 'r') as f:
                content = f.read()
                assert "user@test.com" in content
                assert "(555) 123-4567" in content
                assert "Total Findings: 2" in content

def test_pii_scan_on_project_data():
    """
    Integration test that runs a PII scan on the project's data directories.
    This test verifies that the project's data files do not contain PII.
    """
    base_path = Path(__file__).parent.parent.parent
    data_dirs = [
        base_path / "data" / "raw",
        base_path / "data" / "processed"
    ]
    
    all_findings = []
    
    for data_dir in data_dirs:
        if data_dir.exists():
            findings = scan_directory(data_dir)
            all_findings.extend(findings)
    
    # Generate report
    output_path = base_path / "pii_scan_report.txt"
    generate_report(all_findings, output_path)
    
    # Assert that no PII was found in the project data
    assert len(all_findings) == 0, f"PII detected in project data. See report at {output_path}"