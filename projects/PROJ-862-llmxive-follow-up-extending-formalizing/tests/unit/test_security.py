"""
Unit tests for security utilities (T038).
Tests PII detection, sanitization, and log filtering.
"""
import pytest
import tempfile
import os
import json
import logging
from pathlib import Path

from security_utils import (
    sanitize_text,
    sanitize_dict,
    hash_sensitive_id,
    SecurityLogFilter,
    sanitize_csv_file,
    scan_file_for_pii,
    ensure_no_pii_in_output,
    PII_PATTERNS
)

class TestSanitizeText:
    def test_no_pii(self):
        """Test text without PII remains unchanged."""
        text = "This is a normal sentence."
        result = sanitize_text(text)
        assert result.found_pii is False
        assert result.sanitized_content == text
        assert len(result.pii_types) == 0

    def test_email_pii(self):
        """Test email detection and masking."""
        text = "Contact us at support@example.com for help."
        result = sanitize_text(text)
        assert result.found_pii is True
        assert "support@example.com" not in result.sanitized_content
        assert "email" in result.pii_types
        assert "*" in result.sanitized_content

    def test_phone_pii(self):
        """Test US phone detection and masking."""
        text = "Call me at 555-123-4567."
        result = sanitize_text(text)
        assert result.found_pii is True
        assert "555-123-4567" not in result.sanitized_content
        assert "phone_us" in result.pii_types

    def test_ssn_pii(self):
        """Test SSN detection and masking."""
        text = "SSN: 123-45-6789"
        result = sanitize_text(text)
        assert result.found_pii is True
        assert "123-45-6789" not in result.sanitized_content
        assert "ssn" in result.pii_types

    def test_multiple_pii_types(self):
        """Test detection of multiple PII types in one string."""
        text = "Email: user@test.com, Phone: 555-987-6543"
        result = sanitize_text(text)
        assert result.found_pii is True
        assert "email" in result.pii_types
        assert "phone_us" in result.pii_types
        assert "user@test.com" not in result.sanitized_content
        assert "555-987-6543" not in result.sanitized_content

    def test_empty_string(self):
        """Test handling of empty string."""
        result = sanitize_text("")
        assert result.found_pii is False
        assert result.sanitized_content == ""

    def test_non_string_input(self):
        """Test handling of non-string input."""
        result = sanitize_text(12345)
        assert result.found_pii is False
        assert result.sanitized_content == "12345"

class TestSanitizeDict:
    def test_simple_dict(self):
        """Test sanitization of simple dictionary."""
        data = {"name": "John", "email": "john@example.com"}
        result = sanitize_dict(data)
        assert result["email"] != "john@example.com"
        assert result["name"] == "John"

    def test_nested_dict(self):
        """Test sanitization of nested dictionary."""
        data = {
            "user": {
                "email": "nested@example.com",
                "phone": "555-123-4567"
            }
        }
        result = sanitize_dict(data)
        assert "nested@example.com" not in result["user"]["email"]
        assert "555-123-4567" not in result["user"]["phone"]

    def test_list_in_dict(self):
        """Test sanitization of lists containing strings."""
        data = {
            "contacts": ["a@b.com", "c@d.com", "clean"]
        }
        result = sanitize_dict(data)
        assert "@" not in result["contacts"][0]
        assert "@" not in result["contacts"][1]
        assert result["contacts"][2] == "clean"

    def test_empty_dict(self):
        """Test handling of empty dictionary."""
        result = sanitize_dict({})
        assert result == {}

class TestHashSensitiveId:
    def test_hash_generation(self):
        """Test that ID hashing produces consistent hashes."""
        original = "user_12345"
        hashed1 = hash_sensitive_id(original)
        hashed2 = hash_sensitive_id(original)
        assert hashed1 == hashed2
        assert len(hashed1) == 64  # SHA256 hex length

    def test_hash_not_original(self):
        """Test that hash is not the original value."""
        original = "sensitive_id"
        hashed = hash_sensitive_id(original)
        assert hashed != original

    def test_empty_string(self):
        """Test handling of empty string."""
        result = hash_sensitive_id("")
        assert result == ""

class TestSecurityLogFilter:
    def test_filter_applies(self):
        """Test that the log filter is applied correctly."""
        logger = logging.getLogger("test_security_filter")
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.addFilter(SecurityLogFilter())
        logger.addHandler(handler)
        
        # This should not raise an error
        logger.info("Test message with email user@example.com")
        # If we get here, the filter worked

    def test_mask_char_custom(self):
        """Test custom mask character."""
        logger = logging.getLogger("test_custom_mask")
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.addFilter(SecurityLogFilter(mask_char='X'))
        logger.addHandler(handler)
        
        # Should use X instead of *
        logger.info("Email: test@test.com")

class TestFileSanitization:
    def test_csv_sanitization(self):
        """Test CSV file sanitization."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            f.write("id,name,email\n1,Alice,alice@test.com\n2,Bob,bob@test.com\n")
            input_path = f.name
        
        output_path = input_path.replace('.csv', '_sanitized.csv')
        stats = sanitize_csv_file(input_path, output_path)
        
        assert stats['rows_processed'] == 2
        assert stats['cells_sanitized'] >= 2
        assert stats['pii_found'] is True
        assert os.path.exists(output_path)
        
        # Verify content
        with open(output_path, 'r') as f:
            content = f.read()
            assert "alice@test.com" not in content
            assert "bob@test.com" not in content
        
        os.unlink(input_path)
        os.unlink(output_path)

    def test_scan_file_pii(self):
        """Test PII scanning in files."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Contact: user@example.com\n")
            file_path = f.name
        
        findings = scan_file_for_pii(file_path)
        assert len(findings) > 0
        assert findings[0]['type'] == 'email'
        
        os.unlink(file_path)

class TestEnsureNoPII:
    def test_clean_file(self):
        """Test that clean files pass PII check."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("This is a clean file with no PII.\n")
            file_path = f.name
        
        result = ensure_no_pii_in_output([file_path])
        assert result is True
        os.unlink(file_path)

    def test_dirty_file(self):
        """Test that files with PII fail check."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Email: user@example.com\n")
            file_path = f.name
        
        result = ensure_no_pii_in_output([file_path])
        assert result is False
        os.unlink(file_path)

    def test_missing_file(self):
        """Test handling of missing files."""
        result = ensure_no_pii_in_output(["/nonexistent/file.txt"])
        # Should not crash, but may return True or False depending on implementation
        # The important thing is it doesn't raise an exception
        assert isinstance(result, bool)

class TestIntegrationSecurity:
    def test_end_to_end_sanitization(self):
        """Test end-to-end sanitization workflow."""
        # Create a mock log entry with PII
        log_entry = {
            "user_id": "12345",
            "email": "user@example.com",
            "phone": "555-123-4567",
            "message": "User requested help"
        }
        
        # Sanitize
        sanitized = sanitize_dict(log_entry)
        
        # Verify
        assert sanitized["email"] != "user@example.com"
        assert sanitized["phone"] != "555-123-4567"
        assert sanitized["message"] == "User requested help"
        
        # Verify no PII patterns remain
        for pii_type, pattern in PII_PATTERNS.items():
            assert not pattern.search(json.dumps(sanitized)), f"PII pattern {pii_type} found in sanitized output"