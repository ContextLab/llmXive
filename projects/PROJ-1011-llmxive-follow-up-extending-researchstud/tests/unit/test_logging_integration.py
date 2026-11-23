import pytest
import logging
import os
import sys
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.logging_config import (
    get_logger,
    log_acquisition_failure,
    log_preprocessing_rejection,
    log_preprocessing_rejection_count,
    ensure_log_dir,
    LOG_DIR,
)
from utils.logging_config import log_model_switch, log_memory_error

class TestLoggingIntegration:
    """Test that logging infrastructure correctly captures failures and rejections."""

    def setup_method(self):
        """Ensure log directory exists and reset handlers if needed."""
        ensure_log_dir()
        # Remove existing handlers to avoid duplicates in tests
        for name in ["data_acquisition", "preprocessing", "pipeline"]:
            logger = logging.getLogger(name)
            logger.handlers.clear()

    def test_acquisition_failure_logging(self, caplog):
        """Test that acquisition failures are logged with correct level and message."""
        with caplog.at_level(logging.ERROR):
            log_acquisition_failure("test_source", "http://example.com", "Connection timeout")
        
        assert any("Acquisition failed" in record.message for record in caplog.records)
        assert any("test_source" in record.message for record in caplog.records)
        assert any("http://example.com" in record.message for record in caplog.records)
        assert any("Connection timeout" in record.message for record in caplog.records)
        assert any(record.levelname == "ERROR" for record in caplog.records)

    def test_preprocessing_rejection_logging(self, caplog):
        """Test that preprocessing rejections are logged with correct level and message."""
        with caplog.at_level(logging.WARNING):
            log_preprocessing_rejection("rec_123", "Invalid abstract", "abstract")
        
        assert any("Preprocessing rejected" in record.message for record in caplog.records)
        assert any("rec_123" in record.message for record in caplog.records)
        assert any("Invalid abstract" in record.message for record in caplog.records)
        assert any("Field: abstract" in record.message for record in caplog.records)
        assert any(record.levelname == "WARNING" for record in caplog.records)

    def test_preprocessing_rejection_count_logging(self, caplog):
        """Test that rejection counts are logged."""
        with caplog.at_level(logging.INFO):
            log_preprocessing_rejection_count(100, 5)
        
        assert any("Preprocessing summary" in record.message for record in caplog.records)
        assert any("Processed 100" in record.message for record in caplog.records)
        assert any("Rejected 5" in record.message for record in caplog.records)

    def test_log_file_creation(self):
        """Test that log files are actually created on disk."""
        logger = get_logger("test_file_creation", logging.INFO)
        logger.info("Test message")
        
        log_file = LOG_DIR / "test_file_creation.log"
        assert log_file.exists(), f"Log file {log_file} was not created"
        
        # Clean up
        log_file.unlink()

    def test_model_fallback_logging(self, caplog):
        """Test model switch logging."""
        with caplog.at_level(logging.WARNING):
            log_model_switch("all-MiniLM-L6-v2", "all-distilroberta-v1", "Memory limit")
        
        assert any("Model switch triggered" in record.message for record in caplog.records)
        assert any("all-MiniLM-L6-v2" in record.message for record in caplog.records)
        assert any("all-distilroberta-v1" in record.message for record in caplog.records)
        assert any("Memory limit" in record.message for record in caplog.records)

    def test_memory_error_logging(self, caplog):
        """Test memory error logging."""
        with caplog.at_level(logging.ERROR):
            log_memory_error(7000, 8000)
        
        assert any("Memory constraint hit" in record.message for record in caplog.records)
        assert any("Limit 7000MB" in record.message for record in caplog.records)
        assert any("Requested 8000MB" in record.message for record in caplog.records)