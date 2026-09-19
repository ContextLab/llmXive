import os
import logging
from pathlib import Path

import pytest

from setup_logging import (
    ensure_directories,
    setup_logging,
    get_data_quality_logger,
    get_model_diagnostics_logger,
)


class TestLoggingInfrastructure:
    """Tests for the logging infrastructure setup."""

    def test_ensure_directories_creates_log_dir(self, tmp_path, monkeypatch):
        """Verify that ensure_directories creates the results/logs directory."""
        test_log_dir = tmp_path / "results" / "logs"
        monkeypatch.setenv("RESULTS_LOGS_DIR", str(test_log_dir))

        # Remove the directory if it exists to test creation
        if test_log_dir.exists():
            test_log_dir.rmdir()

        ensure_directories()

        assert test_log_dir.exists()
        assert test_log_dir.is_dir()

    def test_setup_logging_creates_file_handler(self, tmp_path, monkeypatch):
        """Verify that setup_logging creates a file handler."""
        test_log_dir = tmp_path / "results" / "logs"
        test_log_dir.mkdir(parents=True)
        monkeypatch.setenv("RESULTS_LOGS_DIR", str(test_log_dir))

        # Clear root handlers to ensure a clean state
        logging.root.handlers.clear()

        setup_logging(log_file_name="test_pipeline.log")

        file_handlers = [
            h for h in logging.root.handlers if isinstance(h, logging.FileHandler)
        ]
        assert len(file_handlers) == 1
        assert file_handlers[0].baseFilename.endswith("test_pipeline.log")

    def test_get_data_quality_logger(self, tmp_path, monkeypatch):
        """Verify that get_data_quality_logger returns a configured logger."""
        test_log_dir = tmp_path / "results" / "logs"
        test_log_dir.mkdir(parents=True)
        monkeypatch.setenv("RESULTS_LOGS_DIR", str(test_log_dir))

        logger = get_data_quality_logger()

        assert logger.name == "data_quality"
        assert logger.level == logging.INFO
        assert len(logger.handlers) > 0

    def test_get_model_diagnostics_logger(self, tmp_path, monkeypatch):
        """Verify that get_model_diagnostics_logger returns a configured logger."""
        test_log_dir = tmp_path / "results" / "logs"
        test_log_dir.mkdir(parents=True)
        monkeypatch.setenv("RESULTS_LOGS_DIR", str(test_log_dir))

        logger = get_model_diagnostics_logger()

        assert logger.name == "model_diagnostics"
        assert logger.level == logging.INFO
        assert len(logger.handlers) > 0

    def test_log_messages_are_written_to_file(self, tmp_path, monkeypatch):
        """Verify that log messages are actually written to the log file."""
        test_log_dir = tmp_path / "results" / "logs"
        test_log_dir.mkdir(parents=True)
        monkeypatch.setenv("RESULTS_LOGS_DIR", str(test_log_dir))

        logging.root.handlers.clear()
        setup_logging(log_file_name="test_messages.log")

        test_logger = logging.getLogger("test_module")
        test_message = "Test log message for verification"
        test_logger.info(test_message)

        log_file = test_log_dir / "test_messages.log"
        assert log_file.exists()

        content = log_file.read_text()
        assert test_message in content
