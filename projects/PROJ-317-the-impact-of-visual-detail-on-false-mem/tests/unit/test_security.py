"""
Unit tests for security utilities (PII sanitization).
"""
import unittest
from pathlib import Path
import tempfile
import json
import os

# Import the module under test
from utils.security import (
    sanitize_string,
    sanitize_dict,
    sanitize_log_message,
    ensure_log_safety,
    PII_PATTERNS,
    REDACTION_MARKER
)

class TestSanitizeString(unittest.TestCase):
    def test_email_redaction(self):
        text = "Contact user@example.com for help."
        result = sanitize_string(text)
        self.assertIn(REDACTION_MARKER, result)
        self.assertNotIn("user@example.com", result)

    def test_phone_redaction(self):
        text = "Call me at 555-123-4567."
        result = sanitize_string(text)
        self.assertIn(REDACTION_MARKER, result)
        self.assertNotIn("555-123-4567", result)

    def test_ssn_redaction(self):
        text = "SSN: 123-45-6789."
        result = sanitize_string(text)
        self.assertIn(REDACTION_MARKER, result)
        self.assertNotIn("123-45-6789", result)

    def test_uuid_redaction(self):
        text = "ID: 550e8400-e29b-41d4-a716-446655440000."
        result = sanitize_string(text)
        self.assertIn(REDACTION_MARKER, result)
        self.assertNotIn("550e8400-e29b-41d4-a716-446655440000", result)

    def test_no_pii(self):
        text = "This is a safe message with no PII."
        result = sanitize_string(text)
        self.assertEqual(result, text)

    def test_empty_string(self):
        self.assertEqual(sanitize_string(""), "")
        self.assertEqual(sanitize_string(None), None)

class TestSanitizeDict(unittest.TestCase):
    def test_sensitive_key_redaction(self):
        data = {"username": "alice", "password": "secret123"}
        result = sanitize_dict(data, sensitive_keys=["password"])
        self.assertEqual(result["password"], REDACTION_MARKER)
        self.assertEqual(result["username"], "alice") # Not redacted by key, but scanned

    def test_nested_dict(self):
        data = {
            "level1": {
                "level2": {
                    "email": "nested@test.com"
                }
            }
        }
        result = sanitize_dict(data)
        self.assertEqual(result["level1"]["level2"]["email"], REDACTION_MARKER)

    def test_list_with_strings(self):
        data = {"items": ["safe", "bad@email.com", 123]}
        result = sanitize_dict(data)
        self.assertEqual(result["items"][0], "safe")
        self.assertEqual(result["items"][1], REDACTION_MARKER)
        self.assertEqual(result["items"][2], 123)

class TestEnsureLogSafety(unittest.TestCase):
    def test_safe_log_file(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            f.write("This is a safe log message.\n")
            f.write("Another safe line.\n")
            temp_path = f.name

        try:
            self.assertTrue(ensure_log_safety(temp_path))
        finally:
            os.unlink(temp_path)

    def test_unsafe_log_file(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            f.write("User logged in: user@example.com\n")
            temp_path = f.name

        try:
            self.assertFalse(ensure_log_safety(temp_path))
        finally:
            os.unlink(temp_path)

    def test_non_existent_file(self):
        self.assertTrue(ensure_log_safety("/nonexistent/path/file.log"))

class TestSanitizedLoggerIntegration(unittest.TestCase):
    def test_logger_sanitize(self):
        from utils.logging import get_logger
        import logging
        import io
        
        # Create a string buffer to capture logs
        log_stream = io.StringIO()
        
        # Get logger and replace handler temporarily
        logger = get_logger("test_security")
        # Remove existing handlers to avoid clutter
        logger.logger.handlers = []
        
        handler = logging.StreamHandler(log_stream)
        handler.setLevel(logging.INFO)
        logger.logger.addHandler(handler)
        
        logger.info("Contact me at test@example.com")
        
        log_content = log_stream.getvalue()
        self.assertIn(REDACTION_MARKER, log_content)
        self.assertNotIn("test@example.com", log_content)

if __name__ == '__main__':
    unittest.main()
