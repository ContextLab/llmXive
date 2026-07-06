"""
Unit tests for the utils module (logger and config).
"""
import os
import tempfile
from pathlib import Path

import pytest

from src.utils.logger import get_logger, setup_logging
from src.utils.config import Config, get_config, DEFAULT_AR_THRESHOLD


class TestLogger:
    """Tests for the logger module."""

    def test_get_logger_returns_logger(self):
        """Test that get_logger returns a valid Logger instance."""
        logger = get_logger("test_logger")
        assert logger is not None
        assert logger.name == "test_logger"
        assert logger.level == 0  # 0 means NOTSET, inherits from root

    def test_setup_logging_creates_file(self, tmp_path):
        """Test that setup_logging creates a log file."""
        log_dir = tmp_path / "logs"
        log_file = "test.log"

        setup_logging(
            log_level="INFO",
            log_dir=str(log_dir),
            log_file=log_file,
            enable_console=False,
        )

        logger = get_logger("test_setup")
        logger.info("Test message")

        expected_path = log_dir / log_file
        assert expected_path.exists()

        # Check content
        content = expected_path.read_text()
        assert "Test message" in content


class TestConfig:
    """Tests for the config module."""

    def test_config_defaults(self):
        """Test that Config initializes with correct defaults."""
        cfg = Config()
        assert cfg.ar_threshold == DEFAULT_AR_THRESHOLD
        assert cfg.lat_min == 20.0
        assert cfg.lat_max == 60.0
        assert cfg.start_year == 1979
        assert cfg.end_year == 2023

    def test_config_creates_directories(self, tmp_path):
        """Test that Config creates directories if they don't exist."""
        # Change cwd to tmp_path to avoid polluting real FS
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            data_dir = "test_data"
            processed_dir = "test_processed"

            cfg = Config(data_dir=data_dir, processed_dir=processed_dir)

            assert cfg.data_path.exists()
            assert cfg.processed_path.exists()
        finally:
            os.chdir(original_cwd)

    def test_get_config_uses_env_vars(self, monkeypatch, tmp_path):
        """Test that get_config reads from environment variables."""
        test_dir = str(tmp_path / "custom_data")
        monkeypatch.setenv("LLMXIVE_DATA_DIR", test_dir)
        monkeypatch.setenv("LLMXIVE_AR_THRESHOLD", "500.0")
        monkeypatch.setenv("LLMXIVE_START_YEAR", "1980")

        cfg = get_config()

        assert str(cfg.data_path) == Path(test_dir).resolve()
        assert cfg.ar_threshold == 500.0
        assert cfg.start_year == 1980

    def test_config_validate(self, tmp_path):
        """Test that config.validate returns True for writable dirs."""
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            cfg = Config()
            assert cfg.validate() is True
        finally:
            os.chdir(original_cwd)

    def test_config_to_dict(self):
        """Test that config.to_dict returns a dictionary."""
        cfg = Config()
        d = cfg.to_dict()
        assert isinstance(d, dict)
        assert "data_dir" in d
        assert "ar_threshold" in d
