"""
Unit tests for the structured logging infrastructure (T009).

Verifies that:
- Logger can be instantiated
- Error codes follow ERR-### format
- Logs contain correct error codes
- Error registry is properly populated
"""
import pytest
import logging
import sys
from io import StringIO
from pathlib import Path
from code.src.utils.logger import (
    AuditLogger,
    create_logger,
    get_error_message,
    validate_error_code,
    ERROR_CODES,
    get_default_logger,
)


class TestAuditLogger:
    """Tests for the AuditLogger class."""
    
    def test_logger_instantiation(self):
        """Verify logger can be instantiated."""
        logger = AuditLogger()
        assert logger is not None
        assert logger.logger.name == "ab_audit"
    
    def test_logger_with_custom_name(self):
        """Verify logger accepts custom name."""
        logger = AuditLogger(name="custom_test")
        assert logger.logger.name == "custom_test"
    
    def test_logger_with_file(self, tmp_path):
        """Verify logger writes to file when path provided."""
        log_file = tmp_path / "test.log"
        logger = AuditLogger(log_file=log_file)
        assert logger._log_file == log_file
    
    def test_logger_with_level(self):
        """Verify logger accepts custom logging level."""
        logger = AuditLogger(level=logging.DEBUG)
        assert logger.logger.level == logging.DEBUG
    
    def test_log_error_includes_code(self, caplog):
        """Verify error logs include the ERR-### code."""
        logger = AuditLogger()
        logger.log_error("ERR-001", "Test error message")
        
        # Verify error was counted
        assert "ERR-001" in logger.get_error_summary()
        assert logger.get_error_summary()["ERR-001"] == 1
    
    def test_log_error_with_extra_context(self, caplog):
        """Verify error logs can include extra context."""
        logger = AuditLogger()
        logger.log_error("ERR-001", "Test error", url="https://example.com")
        
        # Verify error was counted
        assert "ERR-001" in logger.get_error_summary()
    
    def test_log_warning(self, caplog):
        """Verify warning logs work correctly."""
        logger = AuditLogger()
        logger.log_warning("Test warning")
        
        # Verify warning was logged
        assert any("Test warning" in str(record.msg) for record in caplog.records)
    
    def test_log_info(self, caplog):
        """Verify info logs work correctly."""
        logger = AuditLogger()
        logger.log_info("Test info")
        
        # Verify info was logged
        assert any("Test info" in str(record.msg) for record in caplog.records)
    
    def test_log_debug(self, caplog):
        """Verify debug logs work correctly."""
        logger = AuditLogger(level=logging.DEBUG)
        logger.log_debug("Test debug")
        
        # Verify debug was logged
        assert any("Test debug" in str(record.msg) for record in caplog.records)
    
    def test_get_error_summary(self):
        """Verify error summary returns correct counts."""
        logger = AuditLogger()
        logger.log_error("ERR-001", "First error")
        logger.log_error("ERR-001", "Second error")
        logger.log_error("ERR-002", "Different error")
        
        summary = logger.get_error_summary()
        assert summary["ERR-001"] == 2
        assert summary["ERR-002"] == 1
    
    def test_validate_error_code(self):
        """Verify error code validation works."""
        logger = AuditLogger()
        
        # Valid codes
        assert logger.validate_error_code("ERR-001") is True
        assert logger.validate_error_code("ERR-999") is False
    
    def test_multiple_error_codes_logged(self, caplog):
        """Verify multiple different error codes can be logged."""
        logger = AuditLogger()
        logger.log_error("ERR-001", "First error")
        logger.log_error("ERR-002", "Second error")
        logger.log_error("ERR-003", "Third error")
        
        summary = logger.get_error_summary()
        assert len(summary) == 3
        assert "ERR-001" in summary
        assert "ERR-002" in summary
        assert "ERR-003" in summary


class TestCreateLogger:
    """Tests for the create_logger factory function."""
    
    def test_create_logger_returns_instance(self):
        """Verify create_logger returns AuditLogger instance."""
        logger = create_logger()
        assert isinstance(logger, AuditLogger)
    
    def test_create_logger_with_name(self):
        """Verify create_logger accepts custom name."""
        logger = create_logger(name="test_name")
        assert logger.logger.name == "test_name"
    
    def test_create_logger_with_file(self, tmp_path):
        """Verify create_logger accepts log file path."""
        log_file = tmp_path / "factory.log"
        logger = create_logger(log_file=log_file)
        assert logger._log_file == log_file


class TestGetErrorMessage:
    """Tests for the get_error_message function."""
    
    def test_get_error_message_existing_code(self):
        """Verify error message for existing code."""
        msg = get_error_message("ERR-001")
        assert "Missing required metric" in msg
    
    def test_get_error_message_unknown_code(self):
        """Verify error message for unknown code."""
        msg = get_error_message("ERR-999")
        assert "Unknown error" in msg


class TestValidateErrorCode:
    """Tests for the validate_error_code function."""
    
    def test_validate_existing_code(self):
        """Verify validation for existing code."""
        assert validate_error_code("ERR-001") is True
    
    def test_validate_unknown_code(self):
        """Verify validation for unknown code."""
        assert validate_error_code("ERR-999") is False


class TestErrorCodesRegistry:
    """Tests for the ERROR_CODES registry."""
    
    def test_registry_contains_required_codes(self):
        """Verify registry contains all required error codes."""
        required_codes = [
            "ERR-001", "ERR-002", "ERR-003", "ERR-004", "ERR-005",
            "ERR-006", "ERR-007", "ERR-008", "ERR-009", "ERR-010",
            "ERR-099", "ERR-201", "ERR-301", "ERR-800", "ERR-801",
            "ERR-802", "ERR-950",
        ]
        for code in required_codes:
            assert code in ERROR_CODES, f"Missing error code: {code}"
    
    def test_error_codes_follow_format(self):
        """Verify all error codes follow ERR-### format."""
        import re
        pattern = re.compile(r"^ERR-\d{3}$")
        for code in ERROR_CODES.keys():
            assert pattern.match(code), f"Invalid error code format: {code}"
    
    def test_error_codes_have_descriptions(self):
        """Verify all error codes have non-empty descriptions."""
        for code, msg in ERROR_CODES.items():
            assert msg, f"Empty description for {code}"


class TestDefaultLogger:
    """Tests for the default logger instance."""
    
    def test_get_default_logger_returns_instance(self):
        """Verify get_default_logger returns AuditLogger instance."""
        logger = get_default_logger()
        assert isinstance(logger, AuditLogger)
    
    def test_get_default_logger_returns_same_instance(self):
        """Verify get_default_logger returns singleton instance."""
        logger1 = get_default_logger()
        logger2 = get_default_logger()
        assert logger1 is logger2
