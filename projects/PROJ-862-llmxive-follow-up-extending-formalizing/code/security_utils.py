"""
Unit tests for security utilities (PII sanitization).

Tests verify that:
- PII patterns are correctly detected and redacted
- Sanitization does not break non-PII content
- File sanitization works correctly
- Logging filter prevents PII leaks
"""

import pytest
import json
import csv
import logging
import tempfile
from pathlib import Path
from io import StringIO
from unittest.mock import patch

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from security_utils import (
    sanitize_text,
    sanitize_dict,
    hash_sensitive_id,
    sanitize_csv_file,
    sanitize_json_file,
    SecurityLogFilter,
    scan_file_for_pii,
    ensure_no_pii_in_output,
    EMAIL_REDACTION,
    PHONE_REDACTION,
    IP_REDACTION,
    SSN_REDACTION,
    CREDIT_CARD_REDACTION,
    URL_REDACTION,
    USER_ID_REDACTION,
    API_KEY_REDACTION,
)

class TestSanitizeText:
    """Tests for the sanitize_text function."""

    def test_email_redaction(self):
        """Test that email addresses are redacted."""
        text = "Contact us at support@example.com for help."
        result = sanitize_text(text)
        assert EMAIL_REDACTION in result
        assert "support@example.com" not in result
        assert "Contact us at" in result
        assert "for help" in result
    
    def test_phone_redaction(self):
        """Test that phone numbers are redacted."""
        text = "Call me at 555-123-4567 or 1-800-555-0199."
        result = sanitize_text(text)
        assert result.count(PHONE_REDACTION) >= 1
        assert "555-123-4567" not in result
        assert "1-800-555-0199" not in result
    
    def test_ip_address_redaction(self):
        """Test that IP addresses are redacted."""
        text = "Server at 192.168.1.1 is down."
        result = sanitize_text(text)
        assert IP_REDACTION in result
        assert "192.168.1.1" not in result
    
    def test_ssn_redaction(self):
        """Test that SSN is redacted."""
        text = "SSN: 123-45-6789"
        result = sanitize_text(text)
        assert SSN_REDACTION in result
        assert "123-45-6789" not in result
    
    def test_credit_card_redaction(self):
        """Test that credit card numbers are redacted."""
        text = "Card: 4111-1111-1111-1111"
        result = sanitize_text(text)
        assert CREDIT_CARD_REDACTION in result
        assert "4111-1111-1111-1111" not in result
    
    def test_url_redaction(self):
        """Test that URLs are redacted when enabled."""
        text = "Visit https://example.com/token=secret123 for more info."
        result = sanitize_text(text, redact_urls=True)
        assert URL_REDACTION in result
        assert "https://example.com" not in result
    
    def test_url_not_redacted_by_default(self):
        """Test that URLs are not redacted by default."""
        text = "Visit https://example.com for more info."
        result = sanitize_text(text, redact_urls=False)
        assert URL_REDACTION not in result
        assert "https://example.com" in result
    
    def test_user_id_redaction(self):
        """Test that user IDs are redacted."""
        text = "user_id=abc123xyz or uid=def456"
        result = sanitize_text(text)
        assert USER_ID_REDACTION in result
        assert "abc123xyz" not in result
    
    def test_api_key_redaction(self):
        """Test that API keys are redacted."""
        text = "api_key=sk-12345abcdef or access_token=xyz789"
        result = sanitize_text(text)
        assert API_KEY_REDACTION in result
        assert "sk-12345abcdef" not in result
    
    def test_no_pii_unchanged(self):
        """Test that text without PII remains unchanged."""
        text = "This is a normal sentence with no PII."
        result = sanitize_text(text)
        assert result == text
    
    def test_multiple_pii_types(self):
        """Test sanitization of text with multiple PII types."""
        text = "User john@example.com (555-123-4567) from 192.168.1.1"
        result = sanitize_text(text)
        assert EMAIL_REDACTION in result
        assert PHONE_REDACTION in result
        assert IP_REDACTION in result
        assert "john@example.com" not in result
        assert "555-123-4567" not in result
        assert "192.168.1.1" not in result
    
    def test_non_string_input(self):
        """Test handling of non-string input."""
        assert sanitize_text(123) == "123"
        assert sanitize_text(None) == ""

class TestSanitizeDict:
    """Tests for the sanitize_dict function."""

    def test_simple_dict(self):
        """Test sanitization of a simple dictionary."""
        data = {
            "email": "user@example.com",
            "name": "John Doe"
        }
        result = sanitize_dict(data)
        assert result["email"] == EMAIL_REDACTION
        assert result["name"] == "John Doe"
    
    def test_nested_dict(self):
        """Test sanitization of nested dictionaries."""
        data = {
            "user": {
                "email": "nested@example.com",
                "profile": {
                    "phone": "555-123-4567"
                }
            }
        }
        result = sanitize_dict(data)
        assert result["user"]["email"] == EMAIL_REDACTION
        assert result["user"]["profile"]["phone"] == PHONE_REDACTION
    
    def test_list_in_dict(self):
        """Test sanitization of lists within dictionaries."""
        data = {
            "contacts": [
                "admin@example.com",
                "555-123-4567",
                "normal text"
            ]
        }
        result = sanitize_dict(data)
        assert result["contacts"][0] == EMAIL_REDACTION
        assert result["contacts"][1] == PHONE_REDACTION
        assert result["contacts"][2] == "normal text"

class TestHashSensitiveId:
    """Tests for the hash_sensitive_id function."""

    def test_deterministic_hash(self):
        """Test that the hash is deterministic."""
        value = "user_12345"
        hash1 = hash_sensitive_id(value)
        hash2 = hash_sensitive_id(value)
        assert hash1 == hash2
        assert len(hash1) == 16  # Truncated to 16 chars
    
    def test_different_values_different_hashes(self):
        """Test that different values produce different hashes."""
        hash1 = hash_sensitive_id("user_12345")
        hash2 = hash_sensitive_id("user_67890")
        assert hash1 != hash2
    
    def test_empty_value(self):
        """Test handling of empty values."""
        assert hash_sensitive_id("") == ""

class TestSecurityLogFilter:
    """Tests for the SecurityLogFilter."""

    def test_filter_message(self):
        """Test that the filter sanitizes log messages."""
        filter_obj = SecurityLogFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Email: user@example.com",
            args=(),
            exc_info=None
        )
        filter_obj.filter(record)
        assert EMAIL_REDACTION in record.msg
        assert "user@example.com" not in record.msg
    
    def test_filter_args_dict(self):
        """Test that the filter sanitizes dictionary arguments."""
        filter_obj = SecurityLogFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="User data: %s",
            args=({"email": "user@example.com"},),
            exc_info=None
        )
        filter_obj.filter(record)
        # Args are sanitized in the tuple
        assert EMAIL_REDACTION in str(record.args)
        assert "user@example.com" not in str(record.args)

class TestFileSanitization:
    """Tests for file sanitization functions."""

    def test_csv_sanitization(self):
        """Test CSV file sanitization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.csv"
            output_path = Path(tmpdir) / "output.csv"
            
            # Create input CSV
            with open(input_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['id', 'email', 'phone'])
                writer.writerow(['1', 'user@example.com', '555-123-4567'])
                writer.writerow(['2', 'admin@test.org', '555-987-6543'])
            
            # Sanitize
            sanitize_csv_file(input_path, output_path)
            
            # Verify output
            with open(output_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            assert len(rows) == 2
            assert rows[0]['email'] == EMAIL_REDACTION
            assert rows[0]['phone'] == PHONE_REDACTION
            assert rows[0]['id'] == '1'
    
    def test_json_sanitization(self):
        """Test JSON file sanitization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.json"
            output_path = Path(tmpdir) / "output.json"
            
            # Create input JSON
            data = {
                "user": {
                    "email": "user@example.com",
                    "phone": "555-123-4567"
                },
                "items": ["normal", "user@test.com"]
            }
            with open(input_path, 'w') as f:
                json.dump(data, f)
            
            # Sanitize
            sanitize_json_file(input_path, output_path)
            
            # Verify output
            with open(output_path, 'r') as f:
                result = json.load(f)
            
            assert result["user"]["email"] == EMAIL_REDACTION
            assert result["user"]["phone"] == PHONE_REDACTION
            assert result["items"][1] == EMAIL_REDACTION

class TestPIIScanning:
    """Tests for PII scanning functions."""

    def test_scan_file_detects_pii(self):
        """Test that scanning detects PII in a file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            with open(test_file, 'w') as f:
                f.write("Contact: user@example.com")
            
            result = scan_file_for_pii(test_file)
            assert result['pii_found'] is True
            assert 'email' in result['patterns_detected']
    
    def test_scan_file_no_pii(self):
        """Test scanning a file without PII."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            with open(test_file, 'w') as f:
                f.write("This is normal text with no PII.")
            
            result = scan_file_for_pii(test_file)
            assert result['pii_found'] is False

class TestEnsureNoPII:
    """Tests for the ensure_no_pii_in_output function."""

    def test_verify_clean_file(self):
        """Test verification of a clean file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "clean.txt"
            with open(test_file, 'w') as f:
                f.write("This file has no PII.")
            
            assert ensure_no_pii_in_output(test_file) is True

    def test_verify_pii_file(self):
        """Test verification of a file with PII."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "dirty.txt"
            with open(test_file, 'w') as f:
                f.write("Contact: user@example.com")
            
            assert ensure_no_pii_in_output(test_file) is False

if __name__ == "__main__":
    pytest.main([__file__, "-v"])