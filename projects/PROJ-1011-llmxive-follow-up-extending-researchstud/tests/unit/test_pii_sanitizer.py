"""
Unit tests for the PII Sanitizer module.

These tests verify that the sanitizer correctly detects and redacts
various forms of PII from text, JSON, and CSV data.
"""
import pytest
import json
import csv
import tempfile
import os
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.pii_sanitizer import (
    detect_pii,
    sanitize_text,
    sanitize_file,
    validate_output_file,
    PII_PATTERNS
)

class TestPIIDetection:
    """Tests for PII pattern detection."""

    def test_detect_email(self):
        text = "Contact us at support@example.com or john.doe@test.org"
        findings = detect_pii(text)
        emails = [f for f in findings if f['type'] == 'email']
        assert len(emails) == 2
        assert "support@example.com" in [f['match'] for f in emails]

    def test_detect_phone_us(self):
        text = "Call me at (555) 123-4567 or 555-987-6543"
        findings = detect_pii(text)
        phones = [f for f in findings if f['type'] == 'phone_us']
        assert len(phones) == 2

    def test_detect_ssn(self):
        text = "SSN: 123-45-6789"
        findings = detect_pii(text)
        ssns = [f for f in findings if f['type'] == 'ssn']
        assert len(ssns) == 1
        assert ssns[0]['match'] == "123-45-6789"

    def test_detect_ipv4(self):
        text = "Server IP: 192.168.1.1 and 10.0.0.255"
        findings = detect_pii(text)
        ips = [f for f in findings if f['type'] == 'ipv4']
        assert len(ips) == 2

    def test_detect_orcid(self):
        text = "Researcher ORCID: 0000-0002-1825-0097"
        findings = detect_pii(text)
        orcs = [f for f in findings if f['type'] == 'orcid']
        assert len(orcs) == 1
        assert orcs[0]['match'] == "0000-0002-1825-0097"

    def test_no_false_positives(self):
        # Common words that should not trigger PII
        text = "The cat sat on the mat. It was a nice day."
        findings = detect_pii(text)
        # Should be empty or very few (depending on regex strictness)
        assert len(findings) == 0

    def test_detect_api_key_pattern(self):
        text = "api_key = 'sk-1234567890abcdef1234567890abcdef'"
        findings = detect_pii(text)
        keys = [f for f in findings if f['type'] == 'api_key']
        assert len(keys) == 1

class TestTextSanitization:
    """Tests for text sanitization."""

    def test_sanitize_email(self):
        text = "Email: user@example.com"
        sanitized = sanitize_text(text)
        assert "user@example.com" not in sanitized
        assert "[EMAIL_REDACTED]" in sanitized

    def test_sanitize_multiple_types(self):
        text = "Call 555-123-4567 or email test@test.com"
        sanitized = sanitize_text(text)
        assert "555-123-4567" not in sanitized
        assert "test@test.com" not in sanitized
        assert "[PHONE_REDACTED]" in sanitized
        assert "[EMAIL_REDACTED]" in sanitized

    def test_sanitize_preserves_structure(self):
        text = "Hello, my name is John and I live at 123 Main St."
        sanitized = sanitize_text(text)
        # Should remain unchanged as no PII
        assert sanitized == text

    def test_sanitize_orcid(self):
        text = "ID: 0000-0001-2345-6789"
        sanitized = sanitize_text(text)
        assert "0000-0001-2345-6789" not in sanitized
        assert "[ORCID_REDACTED]" in sanitized

class TestFileSanitization:
    """Tests for file-based sanitization."""

    @pytest.fixture
    def temp_text_file(self):
        content = "Contact: admin@llmxive.org\nIP: 192.168.0.1\nPhone: 555-123-4567"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            path = f.name
        yield path
        os.unlink(path)

    @pytest.fixture
    def temp_json_file(self):
        data = {
            "name": "John Doe",
            "email": "john@example.com",
            "ssn": "123-45-6789",
            "nested": {
                "phone": "555-999-8888"
            }
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            path = f.name
        yield path
        os.unlink(path)

    @pytest.fixture
    def temp_csv_file(self):
        data = [
            {"id": "1", "email": "user1@test.com", "name": "User One"},
            {"id": "2", "email": "user2@test.com", "name": "User Two"}
        ]
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
            path = f.name
        yield path
        os.unlink(path)

    def test_sanitize_text_file(self, temp_text_file):
        output_path = temp_text_file + ".out"
        stats = sanitize_file(temp_text_file, output_path)
        assert stats['pii_found'] == 3
        assert stats['sanitized'] is True
        
        # Verify content
        with open(output_path, 'r') as f:
            content = f.read()
        assert "admin@llmxive.org" not in content
        assert "[EMAIL_REDACTED]" in content
        
        os.unlink(output_path)

    def test_sanitize_json_file(self, temp_json_file):
        output_path = temp_json_file + ".out"
        stats = sanitize_file(temp_json_file, output_path, mode='json')
        assert stats['pii_found'] >= 3
        assert stats['sanitized'] is True
        
        # Verify content
        with open(output_path, 'r') as f:
            data = json.load(f)
        assert data['email'] == "[EMAIL_REDACTED]"
        assert data['nested']['phone'] == "[PHONE_REDACTED]"
        
        os.unlink(output_path)

    def test_sanitize_csv_file(self, temp_csv_file):
        output_path = temp_csv_file + ".out"
        stats = sanitize_file(temp_csv_file, output_path, mode='csv')
        assert stats['pii_found'] == 2
        assert stats['sanitized'] is True
        
        # Verify content
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert rows[0]['email'] == "[EMAIL_REDACTED]"
        
        os.unlink(output_path)

    def test_dry_run(self, temp_text_file):
        output_path = temp_text_file + ".out"
        stats = sanitize_file(temp_text_file, output_path, dry_run=True)
        assert stats['sanitized'] is False
        assert not os.path.exists(output_path)

class TestValidation:
    """Tests for output validation."""

    @pytest.fixture
    def clean_file(self):
        content = "This is a clean file with no PII."
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            path = f.name
        yield path
        os.unlink(path)

    @pytest.fixture
    def dirty_file(self):
        content = "Contact: dirty@test.com"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            path = f.name
        yield path
        os.unlink(path)

    def test_validate_clean_file(self, clean_file):
        assert validate_output_file(clean_file) is True

    def test_validate_dirty_file(self, dirty_file):
        assert validate_output_file(dirty_file) is False

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
