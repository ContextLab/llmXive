import os
import json
import tempfile
import pytest
from pathlib import Path
import csv
import yaml

# Import the functions we're testing
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))
from security_scan import (
    scan_text_for_pii,
    scan_csv_file,
    scan_json_file,
    scan_yaml_file,
    scan_text_file,
    scan_directory
)

class TestPIIScanning:
    """Test PII detection in various file formats."""

    def test_ssn_detection(self):
        """Test SSN pattern detection."""
        text = "Patient SSN: 123-45-6789"
        findings = scan_text_for_pii(text)
        assert len(findings) >= 1
        assert any(f['type'] == 'ssn' for f in findings)

    def test_email_detection(self):
        """Test email pattern detection."""
        text = "Contact: john.doe@example.com"
        findings = scan_text_for_pii(text)
        assert len(findings) >= 1
        assert any(f['type'] == 'email' for f in findings)

    def test_phone_detection(self):
        """Test US phone number detection."""
        text = "Phone: (555) 123-4567"
        findings = scan_text_for_pii(text)
        assert len(findings) >= 1
        assert any(f['type'] == 'phone_us' for f in findings)

    def test_credit_card_detection(self):
        """Test credit card pattern detection."""
        text = "Card: 1234-5678-9012-3456"
        findings = scan_text_for_pii(text)
        assert len(findings) >= 1
        assert any(f['type'] == 'credit_card' for f in findings)

    def test_ip_address_detection(self):
        """Test IP address pattern detection."""
        text = "Server: 192.168.1.1"
        findings = scan_text_for_pii(text)
        assert len(findings) >= 1
        assert any(f['type'] == 'ip_address' for f in findings)

    def test_keyword_detection(self):
        """Test keyword-based detection."""
        text = "This contains medical_record data"
        findings = scan_text_for_pii(text)
        assert len(findings) >= 1
        assert any(f['type'] == 'keyword' for f in findings)

    def test_no_pii(self):
        """Test text with no PII."""
        text = "This is a normal sentence with no sensitive data."
        findings = scan_text_for_pii(text)
        # May still find keywords or common patterns, but should be minimal
        assert len(findings) < 3

class TestCSVScanning:
    """Test CSV file scanning."""

    def test_csv_with_ssn(self):
        """Test CSV containing SSN."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'ssn', 'name'])
            writer.writerow(['1', '123-45-6789', 'John Doe'])
            temp_path = f.name

        try:
            findings = scan_csv_file(temp_path)
            assert len(findings) >= 1
            assert any(f['type'] == 'ssn' for f in findings)
            assert any(f['row'] == 1 for f in findings)  # Row index 1 (data row)
        finally:
            os.unlink(temp_path)

    def test_csv_without_pii(self):
        """Test CSV without PII."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'value', 'name'])
            writer.writerow(['1', '100', 'Item'])
            temp_path = f.name

        try:
            findings = scan_csv_file(temp_path)
            # Should be minimal or no findings
            assert len(findings) < 5
        finally:
            os.unlink(temp_path)

class TestJSONScanning:
    """Test JSON file scanning."""

    def test_json_with_pii(self):
        """Test JSON containing PII."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            data = {
                'name': 'John Doe',
                'email': 'john@example.com',
                'ssn': '123-45-6789'
            }
            json.dump(data, f)
            temp_path = f.name

        try:
            findings = scan_json_file(temp_path)
            assert len(findings) >= 2  # Email and SSN
            types = [f['type'] for f in findings]
            assert 'email' in types
            assert 'ssn' in types
        finally:
            os.unlink(temp_path)

class TestYAMLScanning:
    """Test YAML file scanning."""

    def test_yaml_with_pii(self):
        """Test YAML containing PII."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            data = {
                'contact': {
                    'email': 'admin@example.com',
                    'phone': '555-123-4567'
                }
            }
            yaml.dump(data, f)
            temp_path = f.name

        try:
            findings = scan_yaml_file(temp_path)
            assert len(findings) >= 2  # Email and phone
            types = [f['type'] for f in findings]
            assert 'email' in types
            assert 'phone_us' in types
        finally:
            os.unlink(temp_path)

class TestDirectoryScanning:
    """Test directory scanning."""

    def test_scan_directory(self):
        """Test scanning a directory with multiple file types."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            csv_path = Path(temp_dir) / 'test.csv'
            with open(csv_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['ssn'])
                writer.writerow(['123-45-6789'])

            json_path = Path(temp_dir) / 'test.json'
            with open(json_path, 'w') as f:
                json.dump({'email': 'test@example.com'}, f)

            result = scan_directory(temp_dir)
            
            assert 'summary' in result
            assert result['summary']['total_files_scanned'] == 2
            assert result['summary']['total_findings'] >= 2

    def test_scan_nonexistent_directory(self):
        """Test scanning a non-existent directory."""
        result = scan_directory('/nonexistent/path')
        assert 'error' in result

class TestSeverityLevels:
    """Test severity level assignment."""

    def test_high_severity_ssn(self):
        """Test that SSN is marked as high severity."""
        text = "SSN: 123-45-6789"
        findings = scan_text_for_pii(text)
        ssn_findings = [f for f in findings if f['type'] == 'ssn']
        assert len(ssn_findings) > 0
        assert ssn_findings[0]['severity'] == 'high'

    def test_high_severity_credit_card(self):
        """Test that credit card is marked as high severity."""
        text = "Card: 1234-5678-9012-3456"
        findings = scan_text_for_pii(text)
        cc_findings = [f for f in findings if f['type'] == 'credit_card']
        assert len(cc_findings) > 0
        assert cc_findings[0]['severity'] == 'high'

    def test_medium_severity_email(self):
        """Test that email is marked as medium severity."""
        text = "Email: test@example.com"
        findings = scan_text_for_pii(text)
        email_findings = [f for f in findings if f['type'] == 'email']
        assert len(email_findings) > 0
        assert email_findings[0]['severity'] == 'medium'

    def test_low_severity_keyword(self):
        """Test that keyword matches are marked as low severity."""
        text = "This contains medical_record"
        findings = scan_text_for_pii(text)
        keyword_findings = [f for f in findings if f['type'] == 'keyword']
        assert len(keyword_findings) > 0
        assert keyword_findings[0]['severity'] == 'low'

class TestErrorHandling:
    """Test error handling in scanning functions."""

    def test_scan_invalid_json(self):
        """Test scanning invalid JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{ invalid json }")
            temp_path = f.name

        try:
            findings = scan_json_file(temp_path)
            assert len(findings) >= 1
            assert any(f['type'] == 'error' for f in findings)
        finally:
            os.unlink(temp_path)

    def test_scan_invalid_yaml(self):
        """Test scanning invalid YAML file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content:")
            temp_path = f.name

        try:
            findings = scan_yaml_file(temp_path)
            assert len(findings) >= 1
            assert any(f['type'] == 'error' for f in findings)
        finally:
            os.unlink(temp_path)