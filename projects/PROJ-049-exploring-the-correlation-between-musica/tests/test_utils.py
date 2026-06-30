"""
Tests for code/utils.py
"""

import logging
import os
import tempfile
from pathlib import Path

import pytest

from code.utils import setup_logging, load_config


class TestSetupLogging:
    def test_returns_logger_instance(self):
        """Test that setup_logging returns a logging.Logger instance."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test.log")
            logger = setup_logging(log_file)
            assert isinstance(logger, logging.Logger)
            assert logger.name == "music_personality_logger"

    def test_creates_log_directory(self):
        """Test that setup_logging creates the log directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_log_dir = os.path.join(tmpdir, "nested", "logs")
            log_file = os.path.join(nested_log_dir, "test.log")
            logger = setup_logging(log_file)
            assert os.path.exists(log_file)

    def test_file_rotation_handler(self):
        """Test that the logger has a RotatingFileHandler."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test.log")
            logger = setup_logging(log_file)
            has_rotating_handler = any(
                isinstance(h, logging.handlers.RotatingFileHandler)
                for h in logger.handlers
            )
            assert has_rotating_handler, "Logger should have a RotatingFileHandler"

    def test_console_handler(self):
        """Test that the logger has a StreamHandler for console output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test.log")
            logger = setup_logging(log_file)
            has_stream_handler = any(
                isinstance(h, logging.StreamHandler) for h in logger.handlers
            )
            assert has_stream_handler, "Logger should have a StreamHandler"

    def test_custom_level(self):
        """Test that setup_logging respects the custom level argument."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test.log")
            logger = setup_logging(log_file, level=logging.DEBUG)
            assert logger.level == logging.DEBUG

    def test_env_level_fallback(self):
        """Test that setup_logging falls back to LOG_LEVEL env var."""
        original_level = os.getenv("LOG_LEVEL")
        try:
            os.environ["LOG_LEVEL"] = "WARNING"
            with tempfile.TemporaryDirectory() as tmpdir:
                log_file = os.path.join(tmpdir, "test.log")
                logger = setup_logging(log_file)
                assert logger.level == logging.WARNING
        finally:
            if original_level is None:
                os.environ.pop("LOG_LEVEL", None)
            else:
                os.environ["LOG_LEVEL"] = original_level

class TestLoadConfig:
    def test_returns_dict(self):
        """Test that load_config returns a dictionary."""
        config = load_config()
        assert isinstance(config, dict)

    def test_contains_expected_keys(self):
        """Test that load_config contains the expected keys."""
        config = load_config()
        expected_keys = ["RANDOM_SEED", "DATA_PATH", "LOG_LEVEL"]
        for key in expected_keys:
            assert key in config, f"Config should contain key: {key}"

    def test_defaults_when_missing(self):
        """Test that load_config uses defaults when env vars are missing."""
        # Save original values
        original_values = {
            "RANDOM_SEED": os.getenv("RANDOM_SEED"),
            "DATA_PATH": os.getenv("DATA_PATH"),
            "LOG_LEVEL": os.getenv("LOG_LEVEL"),
        }

        try:
            # Remove env vars
            for key in original_values:
                os.environ.pop(key, None)

            config = load_config()

            # Check defaults
            assert config["RANDOM_SEED"] == 42
            assert config["DATA_PATH"] == "data"
            assert config["LOG_LEVEL"] == "INFO"

        finally:
            # Restore original values
            for key, value in original_values.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
