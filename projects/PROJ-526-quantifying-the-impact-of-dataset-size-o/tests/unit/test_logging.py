import pytest
import logging
from pathlib import Path
import tempfile
import os
import sys

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.logging_config import (
    setup_logging,
    get_logger,
    log_download_progress,
    log_descriptor_stats,
    log_error_summary,
    ResearchFormatter
)

class TestLoggingConfig:
    def test_setup_logging_console_only(self, capsys):
        """Test setting up logging with console output only."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            logger = setup_logging(log_file=log_file, level=logging.INFO, console=True)
            
            assert len(logger.handlers) >= 1
            assert any(isinstance(h, logging.StreamHandler) for h in logger.handlers)
            
            # Verify a log message is captured
            test_logger = get_logger("test_module")
            test_logger.info("Test message")
            
    def test_setup_logging_file_only(self, tmp_path):
        """Test setting up logging with file output only."""
        log_file = tmp_path / "test.log"
        logger = setup_logging(log_file=log_file, level=logging.INFO, console=False)
        
        assert len(logger.handlers) >= 1
        assert any(isinstance(h, logging.FileHandler) for h in logger.handlers)
        
        test_logger = get_logger("test_file_module")
        test_logger.info("File test message")
        
        assert log_file.exists()
        content = log_file.read_text()
        assert "File test message" in content

    def test_log_download_progress(self, caplog):
        """Test download progress logging."""
        caplog.set_level(logging.INFO)
        test_logger = get_logger("test_progress")
        
        log_download_progress(test_logger, 50, 100, "Download")
        
        assert "Download Progress: 50/100 (50.00%)" in caplog.text
        assert "50.0%" in caplog.text  # Progress indicator

    def test_log_descriptor_stats(self, caplog):
        """Test descriptor generation stats logging."""
        caplog.set_level(logging.INFO)
        test_logger = get_logger("test_stats")
        
        log_descriptor_stats(test_logger, "band_gap", 1000, 950, 50)
        
        assert "Descriptor Stats" in caplog.text
        assert "Property: band_gap" in caplog.text
        assert "Total: 1000" in caplog.text
        assert "Valid: 950" in caplog.text
        assert "Missing: 50" in caplog.text
        assert "Success: 95.00%" in caplog.text

    def test_log_descriptor_stats_with_warnings(self, caplog):
        """Test that missing features trigger a warning."""
        caplog.set_level(logging.WARNING)
        test_logger = get_logger("test_warnings")
        
        log_descriptor_stats(test_logger, "elastic", 100, 80, 20)
        
        assert "Property elastic: 20 entries skipped" in caplog.text

    def test_log_error_summary_no_errors(self, caplog):
        """Test error summary when no errors occurred."""
        caplog.set_level(logging.INFO)
        test_logger = get_logger("test_no_errors")
        
        log_error_summary(test_logger, 0, "Download")
        
        assert "Download completed successfully" in caplog.text

    def test_log_error_summary_with_errors(self, caplog):
        """Test error summary when errors occurred."""
        caplog.set_level(logging.ERROR)
        test_logger = get_logger("test_with_errors")
        
        log_error_summary(test_logger, 5, "Processing")
        
        assert "Processing completed with 5 errors" in caplog.text

    def test_research_formatter(self):
        """Test custom formatter with progress indicator."""
        formatter = ResearchFormatter(fmt="%(message)s")
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.progress = "50%"
        
        formatted = formatter.format(record)
        assert "[50%]" in formatted
        assert "Test message" in formatted