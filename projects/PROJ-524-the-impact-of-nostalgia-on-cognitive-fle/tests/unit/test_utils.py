"""
Unit tests for code/utils.py.
"""
import os
import tempfile
import logging
import pytest
from pathlib import Path

# Import the module under test
from utils import (
    setup_logging,
    log_info,
    log_debug,
    log_warning,
    log_error,
    log_critical,
    compute_sha256,
    verify_checksum,
    get_version,
    get_timestamp
)


class TestLogging:
    def test_setup_logging_console_only(self):
        """Test that setup_logging creates a console handler."""
        logger = setup_logging(level=logging.INFO)
        assert logger.name == "nostalgia_cognitive"
        assert len(logger.handlers) >= 1
        
        # Verify console handler exists
        has_console = any(
            isinstance(h, logging.StreamHandler) and 
            not isinstance(h, logging.FileHandler)
            for h in logger.handlers
        )
        assert has_console

    def test_setup_logging_with_file(self):
        """Test that setup_logging creates a file handler when path is provided."""
        with tempfile.NamedTemporaryFile(suffix='.log', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            logger = setup_logging(level=logging.INFO, log_file=tmp_path)
            has_file = any(
                isinstance(h, logging.FileHandler)
                for h in logger.handlers
            )
            assert has_file
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_log_levels(self):
        """Test that all log level helpers work."""
        logger = setup_logging(level=logging.DEBUG)
        
        # These should not raise exceptions
        log_info(logger, "Test info")
        log_debug(logger, "Test debug")
        log_warning(logger, "Test warning")
        log_error(logger, "Test error")
        log_critical(logger, "Test critical")


class TestChecksum:
    def test_compute_sha256(self):
        """Test SHA-256 computation on a known file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp:
            tmp.write("Hello, World!")
            tmp_path = tmp.name
        
        try:
            checksum = compute_sha256(tmp_path)
            # Known SHA-256 for "Hello, World!"
            expected = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
            assert checksum == expected
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_verify_checksum_true(self):
        """Test verify_checksum returns True for correct checksum."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp:
            tmp.write("Test content")
            tmp_path = tmp.name
        
        try:
            checksum = compute_sha256(tmp_path)
            assert verify_checksum(tmp_path, checksum) is True
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_verify_checksum_false(self):
        """Test verify_checksum returns False for incorrect checksum."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp:
            tmp.write("Test content")
            tmp_path = tmp.name
        
        try:
            assert verify_checksum(tmp_path, "invalid_checksum") is False
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


class TestVersioning:
    def test_get_version(self):
        """Test that get_version returns a string."""
        version = get_version()
        assert isinstance(version, str)
        assert len(version) > 0

    def test_get_timestamp(self):
        """Test that get_timestamp returns a valid ISO format string."""
        timestamp = get_timestamp()
        assert isinstance(timestamp, str)
        assert len(timestamp) > 0
        # Basic check for ISO format (contains 'T' or '-' or ':')
        assert any(c in timestamp for c in ['T', '-', ':'])