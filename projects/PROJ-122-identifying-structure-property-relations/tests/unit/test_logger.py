"""
Unit tests for the logging infrastructure (T007).

Tests verify:
- Logger initialization and configuration
- Log file creation
- Console logging
- Checksum logging functionality
- PipelineLogger context awareness
"""

import os
import sys
import tempfile
import logging
from pathlib import Path
from datetime import datetime

import pytest

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.logger import (
    setup_logging,
    get_logger,
    log_artifact_checksum,
    PipelineLogger,
    DEFAULT_FORMAT,
    DEFAULT_LEVEL,
    LOG_DIR
)
from utils.seeds import set_deterministic_seed


class TestSetupLogging:
    """Tests for setup_logging function."""

    def test_default_configuration(self, tmp_path, monkeypatch):
        """Test logger setup with default settings."""
        # Change to temp directory to avoid cluttering project state
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("LOG_LEVEL", "INFO")

        logger = setup_logging(console=True, log_file=tmp_path / "test.log")

        assert logger.level == logging.INFO
        assert len(logger.handlers) == 2  # Console + File
        
        # Verify file handler exists
        file_handler = next(
            (h for h in logger.handlers if isinstance(h, logging.FileHandler)),
            None
        )
        assert file_handler is not None
        assert file_handler.baseFilename == str(tmp_path / "test.log")

    def test_custom_log_level(self, tmp_path, monkeypatch):
        """Test logger setup with custom log level."""
        monkeypatch.chdir(tmp_path)
        
        logger = setup_logging(
            level=logging.DEBUG,
            log_file=tmp_path / "debug.log",
            console=False
        )

        assert logger.level == logging.DEBUG

    def test_no_console_handler(self, tmp_path, monkeypatch):
        """Test logger setup without console output."""
        monkeypatch.chdir(tmp_path)
        
        logger = setup_logging(
            log_file=tmp_path / "file_only.log",
            console=False
        )

        assert len(logger.handlers) == 1
        assert isinstance(logger.handlers[0], logging.FileHandler)

    def test_custom_format(self, tmp_path, monkeypatch):
        """Test logger setup with custom format."""
        monkeypatch.chdir(tmp_path)
        custom_format = "%(levelname)s - %(message)s"
        
        logger = setup_logging(
            format_str=custom_format,
            log_file=tmp_path / "custom.log",
            console=False
        )

        formatter = logger.handlers[0].formatter
        assert formatter._fmt == custom_format

    def test_environment_variable_level(self, tmp_path, monkeypatch):
        """Test that LOG_LEVEL environment variable is respected."""
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("LOG_LEVEL", "WARNING")
        
        logger = setup_logging(log_file=tmp_path / "env.log", console=False)
        
        assert logger.level == logging.WARNING


class TestGetLogger:
    """Tests for get_logger function."""

    def test_get_root_logger(self, tmp_path, monkeypatch):
        """Test getting the root logger."""
        monkeypatch.chdir(tmp_path)
        setup_logging(log_file=tmp_path / "root.log", console=False)
        
        root_logger = get_logger()
        assert root_logger.name == ""
        assert isinstance(root_logger, logging.Logger)

    def test_get_named_logger(self, tmp_path, monkeypatch):
        """Test getting a named logger."""
        monkeypatch.chdir(tmp_path)
        setup_logging(log_file=tmp_path / "named.log", console=False)
        
        named_logger = get_logger("my_module")
        assert named_logger.name == "my_module"
        assert isinstance(named_logger, logging.Logger)


class TestLogArtifactChecksum:
    """Tests for log_artifact_checksum function."""

    def test_valid_file(self, tmp_path, monkeypatch, caplog):
        """Test checksum logging for a valid file."""
        monkeypatch.chdir(tmp_path)
        setup_logging(log_file=tmp_path / "checksum.log", console=False)
        logger = get_logger()

        # Create a test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")

        with caplog.at_level(logging.INFO):
            checksum = log_artifact_checksum(logger, test_file, "test_artifact")

        assert len(checksum) == 64  # SHA-256 hex length
        assert "test_artifact" in caplog.text
        assert checksum in caplog.text

    def test_nonexistent_file(self, tmp_path, monkeypatch):
        """Test checksum logging for a non-existent file raises error."""
        monkeypatch.chdir(tmp_path)
        setup_logging(log_file=tmp_path / "error.log", console=False)
        logger = get_logger()

        nonexistent = tmp_path / "does_not_exist.txt"
        
        with pytest.raises(FileNotFoundError):
            log_artifact_checksum(logger, nonexistent)


class TestPipelineLogger:
    """Tests for PipelineLogger context-aware wrapper."""

    def test_start_and_complete(self, tmp_path, monkeypatch, caplog):
        """Test start and complete logging."""
        monkeypatch.chdir(tmp_path)
        setup_logging(log_file=tmp_path / "pipeline.log", console=False)
        
        pipeline_logger = PipelineLogger("test_stage")

        with caplog.at_level(logging.INFO):
            pipeline_logger.start()
            # Simulate some work
            import time
            time.sleep(0.01)
            pipeline_logger.complete()

        assert "Starting stage: test_stage" in caplog.text
        assert "Completed stage: test_stage" in caplog.text
        assert "duration" in caplog.text

    def test_fail_logging(self, tmp_path, monkeypatch, caplog):
        """Test failure logging with exception."""
        monkeypatch.chdir(tmp_path)
        setup_logging(log_file=tmp_path / "fail.log", console=False)
        
        pipeline_logger = PipelineLogger("failing_stage")

        with caplog.at_level(logging.ERROR):
            pipeline_logger.start()
            try:
                raise ValueError("Test error")
            except ValueError as e:
                pipeline_logger.fail(e)

        assert "Failed stage: failing_stage" in caplog.text
        assert "Test error" in caplog.text

    def test_custom_kwargs(self, tmp_path, monkeypatch, caplog):
        """Test logging with custom keyword arguments."""
        monkeypatch.chdir(tmp_path)
        setup_logging(log_file=tmp_path / "kwargs.log", console=False)
        
        pipeline_logger = PipelineLogger("custom_stage")

        with caplog.at_level(logging.INFO):
            pipeline_logger.start(extra_param="test_value")
            pipeline_logger.complete(result_count=100)

        assert "extra_param" in caplog.text
        assert "test_value" in caplog.text
        assert "result_count" in caplog.text
        assert "100" in caplog.text