import os
import pytest
from pathlib import Path
import logging

from code.setup_data_dirs import main as setup_data_dirs_main
from code.setup_logging import setup_logging, get_logger

class TestDataDirectories:
    """Tests for data directory structure setup."""

    def test_data_raw_exists(self):
        """Verify data/raw/ directory exists after setup."""
        result = setup_data_dirs_main()
        assert result == 0
        assert Path("data/raw").exists()
        assert Path("data/raw").is_dir()

    def test_data_processed_exists(self):
        """Verify data/processed/ directory exists after setup."""
        result = setup_data_dirs_main()
        assert result == 0
        assert Path("data/processed").exists()
        assert Path("data/processed").is_dir()

    def test_data_logs_exists(self):
        """Verify data/logs/ directory exists after setup."""
        result = setup_data_dirs_main()
        assert result == 0
        assert Path("data/logs").exists()
        assert Path("data/logs").is_dir()

    def test_data_figures_exists(self):
        """Verify data/figures/ directory exists after setup."""
        result = setup_data_dirs_main()
        assert result == 0
        assert Path("data/figures").exists()
        assert Path("data/figures").is_dir()

class TestLoggingInfrastructure:
    """Tests for logging infrastructure setup."""

    def test_setup_logging_creates_handlers(self):
        """Verify setup_logging configures console and file handlers."""
        logger = setup_logging(level=logging.INFO)
        
        # Check that handlers are present
        assert len(logger.handlers) >= 2, "Logger should have at least 2 handlers (console + file)"
        
        # Check for file handler
        file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) > 0, "Logger should have a file handler"

    def test_setup_logging_creates_log_file(self):
        """Verify setup_logging creates an actual log file."""
        logger = setup_logging(level=logging.INFO)
        
        # Find the file handler
        file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) > 0
        
        log_file_path = Path(file_handlers[0].baseFilename)
        assert log_file_path.exists(), f"Log file should exist at {log_file_path}"

    def test_get_logger_returns_valid_logger(self):
        """Verify get_logger returns a valid logger instance."""
        logger = get_logger("test_module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_module"

    def test_get_logger_default(self):
        """Verify get_logger() with no args returns root logger."""
        root_logger = logging.getLogger()
        logger = get_logger()
        assert logger is root_logger

    def test_log_message_written_to_file(self, tmp_path):
        """Verify log messages are written to the log file."""
        # Use a temporary log file for this test
        log_file = tmp_path / "test.log"
        logger = setup_logging(level=logging.INFO, log_file=str(log_file))
        
        # Log a message
        test_msg = "Test log message for verification"
        logger.info(test_msg)
        
        # Verify the file exists and contains the message
        assert log_file.exists()
        content = log_file.read_text()
        assert test_msg in content