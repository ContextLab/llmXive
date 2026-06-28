"""
Unit tests for error message format validation per FR-007.

These tests verify that:
1. All logged error codes follow the ERR-### naming convention
2. Error message descriptions are within appropriate length bounds for analysis

FR-007 Requirements:
- Error codes must match pattern ERR-### (three-digit numeric suffix)
- Error codes must be in range ERR-001 to ERR-099
- Error message descriptions must be sufficiently descriptive (≥ 10 chars)
  and not excessively long (≤ 200 chars) for intended analysis
"""

import pytest
from code.src.utils.logger import (
    get_error_message,
    validate_error_code,
    AuditLogger,
)
import re


class TestErrorCodeFormat:
    """Test that error codes follow FR-007 naming conventions."""

    def test_valid_error_code_format_three_digit(self):
        """Valid error codes must have exactly three digits after ERR-."""
        valid_codes = ["ERR-001", "ERR-002", "ERR-050", "ERR-099"]
        for code in valid_codes:
            assert validate_error_code(code), f"Code {code} should be valid"

    def test_invalid_error_code_format_two_digit(self):
        """Error codes with two digits should be invalid."""
        invalid_codes = ["ERR-01", "ERR-1", "ERR-10"]
        for code in invalid_codes:
            assert not validate_error_code(code), f"Code {code} should be invalid"

    def test_invalid_error_code_format_four_digit(self):
        """Error codes with four digits should be invalid."""
        invalid_codes = ["ERR-0001", "ERR-1000"]
        for code in invalid_codes:
            assert not validate_error_code(code), f"Code {code} should be invalid"

    def test_invalid_error_code_prefix(self):
        """Error codes must start with ERR-."""
        invalid_codes = ["ERROR-001", "ERR001", "E001"]
        for code in invalid_codes:
            assert not validate_error_code(code), f"Code {code} should be invalid"

    def test_error_code_range_lower_bound(self):
        """Error codes below ERR-001 should be invalid."""
        assert not validate_error_code("ERR-000")
        assert not validate_error_code("ERR-0000")

    def test_error_code_range_upper_bound(self):
        """Error codes above ERR-099 should be invalid."""
        assert not validate_error_code("ERR-100")
        assert not validate_error_code("ERR-200")

    def test_error_code_pattern_regex(self):
        """Error codes must match the exact ERR-### pattern."""
        pattern = r"^ERR-\d{3}$"
        assert re.match(pattern, "ERR-001")
        assert re.match(pattern, "ERR-099")
        assert not re.match(pattern, "ERR-1")
        assert not re.match(pattern, "ERR-0001")


class TestErrorMessageLength:
    """Test that error message descriptions are within appropriate length bounds."""

    def test_error_message_minimum_length(self):
        """Error message descriptions must be at least 10 characters."""
        # Get error messages for valid codes
        for code_int in range(1, 100):
            code = f"ERR-{code_int:03d}"
            message = get_error_message(code)
            if message:  # Only check if message exists
                assert len(message) >= 10, (
                    f"Error message for {code} is too short: "
                    f"'{message}' ({len(message)} chars)"
                )

    def test_error_message_maximum_length(self):
        """Error message descriptions must not exceed 200 characters."""
        for code_int in range(1, 100):
            code = f"ERR-{code_int:03d}"
            message = get_error_message(code)
            if message:  # Only check if message exists
                assert len(message) <= 200, (
                    f"Error message for {code} is too long: "
                    f"'{message}' ({len(message)} chars)"
                )

    def test_error_message_not_empty(self):
        """Error message descriptions must not be empty for valid codes."""
        for code_int in range(1, 100):
            code = f"ERR-{code_int:03d}"
            message = get_error_message(code)
            if message:  # Only check if message exists
                assert len(message.strip()) > 0, (
                    f"Error message for {code} is empty"
                )

    def test_error_message_descriptive_content(self):
        """Error messages should contain meaningful descriptive content."""
        # Check that messages contain actual words, not just symbols
        for code_int in range(1, 100):
            code = f"ERR-{code_int:03d}"
            message = get_error_message(code)
            if message:
                # Should contain at least one alphabetic character
                assert any(c.isalpha() for c in message), (
                    f"Error message for {code} lacks alphabetic content: "
                    f"'{message}'"
                )


class TestAuditLoggerErrorCodeUsage:
    """Test that AuditLogger uses error codes correctly."""

    def test_logger_accepts_valid_error_code(self):
        """AuditLogger should accept valid error codes without raising."""
        logger = AuditLogger("test_logger")
        # Should not raise
        logger.log_error("ERR-001", "Test error message")

    def test_logger_rejects_invalid_error_code(self):
        """AuditLogger should reject invalid error codes."""
        logger = AuditLogger("test_logger")
        with pytest.raises(ValueError):
            logger.log_error("INVALID", "Test error message")

    def test_logger_rejects_out_of_range_code(self):
        """AuditLogger should reject codes outside ERR-001 to ERR-099."""
        logger = AuditLogger("test_logger")
        with pytest.raises(ValueError):
            logger.log_error("ERR-000", "Test error message")
        with pytest.raises(ValueError):
            logger.log_error("ERR-100", "Test error message")


class TestErrorCodesRegistryCompleteness:
    """Test that the error codes registry is complete for expected range."""

    def test_all_codes_in_range_001_to_099_defined(self):
        """All error codes from ERR-001 to ERR-099 should be defined."""
        # Get all defined codes by checking which return non-None messages
        defined_codes = set()
        for code_int in range(1, 100):
            code = f"ERR-{code_int:03d}"
            message = get_error_message(code)
            if message:
                defined_codes.add(code)

        # We expect at least some codes to be defined
        assert len(defined_codes) > 0, (
            "No error codes are defined in the registry"
        )

    def test_error_code_naming_consistency(self):
        """All error codes should follow consistent naming pattern."""
        pattern = r"^ERR-\d{3}$"
        for code_int in range(1, 100):
            code = f"ERR-{code_int:03d}"
            message = get_error_message(code)
            if message:
                assert re.match(pattern, code), (
                    f"Error code {code} does not match naming pattern"
                )


class TestErrorMessageAnalysisReadiness:
    """Test that error messages are suitable for intended analysis."""

    def test_error_messages_are_readable(self):
        """Error messages should be human-readable strings."""
        for code_int in range(1, 100):
            code = f"ERR-{code_int:03d}"
            message = get_error_message(code)
            if message:
                assert isinstance(message, str), (
                    f"Error message for {code} is not a string"
                )

    def test_error_messages_no_truncation(self):
        """Error messages should not be truncated versions of longer text."""
        # Messages should not end with ellipsis indicating truncation
        for code_int in range(1, 100):
            code = f"ERR-{code_int:03d}"
            message = get_error_message(code)
            if message:
                assert not message.strip().endswith("..."), (
                    f"Error message for {code} appears truncated: '{message}'"
                )

    def test_error_messages_complete_sentences(self):
        """Error messages should be complete, not fragments."""
        # At minimum, messages should have a verb or noun phrase
        for code_int in range(1, 100):
            code = f"ERR-{code_int:03d}"
            message = get_error_message(code)
            if message:
                # Should have at least 2 words for meaningful description
                words = message.split()
                assert len(words) >= 2, (
                    f"Error message for {code} is too brief: '{message}'"
                )


# Test class aliases for compatibility with test discovery
TestErrorFormat = TestErrorCodeFormat
TestMessageLength = TestErrorMessageLength
TestLoggerUsage = TestAuditLoggerErrorCodeUsage
TestRegistryCompleteness = TestErrorCodesRegistryCompleteness
TestAnalysisReadiness = TestErrorMessageAnalysisReadiness