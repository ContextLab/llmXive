"""
Unit tests for the logging infrastructure.

Tests cover:
- Log initialization
- PII masking
- Log rotation setup
- Logger retrieval
"""
import os
import sys
import tempfile
import logging
from pathlib import Path
import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.utils.logging import (
    setup_logging,
    get_logger,
    mask_pii,
    PIIFilter,
    get_log_directory,
    _setup_done
)

class TestPIIMasking:
    """Tests for PII masking functionality."""
    
    def test_mask_email(self):
        """Test that email addresses are masked."""
        message = "Contact user@example.com for details"
        masked = mask_pii(message)
        assert 'user@example.com' not in masked
        assert '[EMAIL_REDACTED]' in masked
    
    def test_mask_github_token(self):
        """Test that GitHub tokens are masked."""
        message = "Token: ghp_abcdefghijklmnopqrstuvwxyz1234567890"
        masked = mask_pii(message)
        assert 'ghp_' not in masked
        assert '[GITHUB_TOKEN_REDACTED]' in masked
    
    def test_mask_api_key(self):
        """Test that API keys are masked."""
        message = "api_key=abcdefghij1234567890abcdefghij"
        masked = mask_pii(message)
        assert 'api_key=' not in masked.lower() or '[API_KEY_REDACTED]' in masked
    
    def test_no_false_positives(self):
        """Test that normal text is not masked."""
        message = "The quick brown fox jumps over the lazy dog"
        masked = mask_pii(message)
        assert masked == message
    
    def test_multiple_pii_types(self):
        """Test masking of multiple PII types in one message."""
        message = "User test@example.com with token ghp_abc123def456"
        masked = mask_pii(message)
        assert 'test@example.com' not in masked
        assert 'ghp_' not in masked
        assert masked.count('[REDACTED]') >= 2

class TestLoggingSetup:
    """Tests for logging initialization."""
    
    @pytest.fixture(autouse=True)
    def reset_logging_state(self):
        """Reset logging state before each test."""
        # Note: In real tests, we'd need to properly reset the global state
        # This is a simplified version
        yield
    
    def test_setup_logging_creates_directory(self, tmp_path):
        """Test that setup_logging creates the log directory."""
        log_dir = tmp_path / "test_logs"
        setup_logging(log_dir=log_dir)
        assert log_dir.exists()
    
    def test_setup_logging_creates_file(self, tmp_path):
        """Test that setup_logging creates the main log file."""
        log_dir = tmp_path / "test_logs"
        setup_logging(log_dir=log_dir)
        log_file = log_dir / "pipeline.log"
        # The file might not exist until a log is written, but the handler should be configured
        # We'll test by actually logging something
        logger = get_logger("test_setup")
        logger.info("Test message")
        assert log_file.exists()
    
    def test_get_logger_returns_logger(self):
        """Test that get_logger returns a valid logger instance."""
        # Ensure setup is done
        with tempfile.TemporaryDirectory() as tmp_dir:
            setup_logging(log_dir=Path(tmp_dir))
            logger = get_logger("test_module")
            assert isinstance(logger, logging.Logger)
            assert logger.name == "test_module"
    
    def test_logger_has_handlers(self):
        """Test that the logger has handlers configured."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            setup_logging(log_dir=Path(tmp_dir))
            logger = get_logger("test_handlers")
            assert len(logger.handlers) > 0 or len(logging.getLogger().handlers) > 0

class TestPIIFilter:
    """Tests for the PII filter class."""
    
    def test_filter_masks_email_in_record(self):
        """Test that PII filter masks email in log record."""
        filter_instance = PIIFilter()
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=1,
            msg='Contact user@example.com',
            args=(),
            exc_info=None
        )
        result = filter_instance.filter(record)
        assert result is True
        assert 'user@example.com' not in record.msg
        assert '[EMAIL_REDACTED]' in record.msg
    
    def test_filter_allows_record_through(self):
        """Test that filter allows record through after masking."""
        filter_instance = PIIFilter()
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=1,
            msg='Normal message',
            args=(),
            exc_info=None
        )
        result = filter_instance.filter(record)
        assert result is True

class TestLogDirectory:
    """Tests for log directory management."""
    
    def test_get_log_directory_returns_path(self, tmp_path):
        """Test that get_log_directory returns the configured path."""
        log_dir = tmp_path / "test_logs"
        setup_logging(log_dir=log_dir)
        result = get_log_directory()
        assert result == log_dir

class TestLoggingIntegration:
    """Integration tests for logging functionality."""
    
    def test_log_message_appears_in_file(self, tmp_path):
        """Test that log messages appear in the log file."""
        log_dir = tmp_path / "test_logs"
        setup_logging(log_dir=log_dir)
        
        logger = get_logger("test_integration")
        test_message = "Integration test message"
        logger.info(test_message)
        
        log_file = log_dir / "pipeline.log"
        assert log_file.exists()
        
        with open(log_file, 'r') as f:
            content = f.read()
            assert test_message in content
    
    def test_pii_masked_in_log_file(self, tmp_path):
        """Test that PII is masked in the log file."""
        log_dir = tmp_path / "test_logs"
        setup_logging(log_dir=log_dir)
        
        logger = get_logger("test_pii")
        test_message = "Contact admin@test.com for help"
        logger.info(test_message)
        
        log_file = log_dir / "pipeline.log"
        with open(log_file, 'r') as f:
            content = f.read()
            assert 'admin@test.com' not in content
            assert '[EMAIL_REDACTED]' in content
