"""
Tests for utility functions in code/utils.py.
"""

import logging
import os
import tempfile
from pathlib import Path

import pytest

from code.utils import (
    setup_logging,
    load_config,
    compute_file_checksum,
    verify_checksum,
    _resolve_log_level,
)


class TestResolveLogLevel:
    """Tests for the _resolve_log_level helper function."""

    def test_integer_level(self):
        """Test that integer levels are passed through."""
        assert _resolve_log_level(logging.INFO) == logging.INFO
        assert _resolve_log_level(logging.DEBUG) == logging.DEBUG

    def test_string_level_upper(self):
        """Test that uppercase string levels are resolved correctly."""
        assert _resolve_log_level("INFO") == logging.INFO
        assert _resolve_log_level("DEBUG") == logging.DEBUG
        assert _resolve_log_level("WARNING") == logging.WARNING
        assert _resolve_log_level("ERROR") == logging.ERROR
        assert _resolve_log_level("CRITICAL") == logging.CRITICAL

    def test_string_level_lower(self):
        """Test that lowercase string levels are resolved correctly."""
        assert _resolve_log_level("info") == logging.INFO
        assert _resolve_log_level("debug") == logging.DEBUG

    def test_string_level_warn_alias(self):
        """Test that WARN is resolved to WARNING."""
        assert _resolve_log_level("WARN") == logging.WARNING
        assert _resolve_log_level("warn") == logging.WARNING

    def test_invalid_string_level(self):
        """Test that invalid string levels raise ValueError."""
        with pytest.raises(ValueError, match="Unknown level"):
            _resolve_log_level("INVALID_LEVEL")

    def test_invalid_type(self):
        """Test that invalid types raise ValueError."""
        with pytest.raises(ValueError, match="Unknown level type"):
            _resolve_log_level(3.14)


class TestSetupLogging:
    """Tests for the setup_logging function."""

    def test_default_level(self):
        """Test that setup_logging returns a logger with default INFO level."""
        logger = setup_logging()
        assert logger.name == "llmXive"
        assert logger.level == logging.INFO

    def test_string_level(self):
        """Test that setup_logging accepts a string level."""
        logger = setup_logging("DEBUG")
        assert logger.level == logging.DEBUG

    def test_invalid_string_level_raises(self):
        """Test that setup_logging raises on invalid string level."""
        with pytest.raises(ValueError):
            setup_logging("INVALID")

    def test_file_handler_creation(self):
        """Test that a file handler is created when log_file is provided."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test.log"
            logger = setup_logging(log_file=log_path)
            
            # Check that file exists and handler is present
            assert log_path.exists()
            assert any(isinstance(h, logging.FileHandler) for h in logger.handlers)

    def test_duplicate_handler_prevention(self):
        """Test that calling setup_logging multiple times doesn't duplicate handlers."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test.log"
            
            # Call twice
            logger1 = setup_logging(log_file=log_path)
            logger2 = setup_logging(log_file=log_path)
            
            # Count handlers (should not increase significantly if cleared properly)
            # Note: In a real run, we clear handlers, so count should be stable
            handler_count = len(logger2.handlers)
            assert handler_count <= 2  # Console + File


class TestLoadConfig:
    """Tests for the load_config function."""

    def test_missing_config_returns_empty(self):
        """Test that missing config returns empty dict."""
        result = load_config(Path("/nonexistent/config.yaml"))
        assert result == {}

    def test_valid_config(self):
        """Test loading a valid YAML config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            config_content = """
            test_key: test_value
            number: 42
            nested:
              key: value
            """
            config_path.write_text(config_content)
            
            result = load_config(config_path)
            assert result["test_key"] == "test_value"
            assert result["number"] == 42
            assert result["nested"]["key"] == "value"


class TestChecksum:
    """Tests for checksum functions."""

    def test_compute_checksum(self):
        """Test checksum computation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.txt"
            content = "Hello, World!"
            file_path.write_text(content)
            
            checksum = compute_file_checksum(file_path)
            assert len(checksum) == 64  # SHA256 hex length
            assert all(c in '0123456789abcdef' for c in checksum)

    def test_verify_checksum_match(self):
        """Test checksum verification when matching."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.txt"
            content = "Hello, World!"
            file_path.write_text(content)
            
            checksum = compute_file_checksum(file_path)
            assert verify_checksum(file_path, checksum) is True

    def test_verify_checksum_mismatch(self):
        """Test checksum verification when not matching."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.txt"
            file_path.write_text("Hello, World!")
            
            assert verify_checksum(file_path, "wrong_checksum") is False