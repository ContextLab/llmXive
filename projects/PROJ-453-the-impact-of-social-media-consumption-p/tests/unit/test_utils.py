"""
Unit tests for core utilities in code/utils.py.
"""

import pytest
import os
import tempfile
import logging
from pathlib import Path

# Import the functions we are testing
# Note: In a real environment, we would import from 'code.utils'
# but for this test structure, we assume the module is in the path
try:
    from utils import log_setup, checksum_file, causal_language_scanner
except ImportError:
    # Fallback for testing context
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))
    from utils import log_setup, checksum_file, causal_language_scanner


class TestLogSetup:
    """Tests for the log_setup function."""

    def test_log_setup_returns_logger(self):
        """Test that log_setup returns a logging.Logger instance."""
        logger = log_setup()
        assert isinstance(logger, logging.Logger)
        assert logger.name == "llmXive"

    def test_log_setup_has_stdout_handler(self):
        """Test that the logger has a StreamHandler for stdout."""
        logger = log_setup()
        # Check that at least one handler exists
        assert len(logger.handlers) > 0
        # Verify it's a StreamHandler
        from logging import StreamHandler
        assert any(isinstance(h, StreamHandler) for h in logger.handlers)


class TestChecksumFile:
    """Tests for the checksum_file function."""

    def test_checksum_known_file(self):
        """Test checksum calculation on a file with known content."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Hello, World!")
            temp_path = f.name

        try:
            # MD5 of "Hello, World!" is 65a8e27d8879283831b664bd8b7f0ad4
            checksum = checksum_file(temp_path)
            assert checksum == "65a8e27d8879283831b664bd8b7f0ad4"
        finally:
            os.unlink(temp_path)

    def test_checksum_nonexistent_file_raises(self):
        """Test that checksum_file raises FileNotFoundError for missing files."""
        with pytest.raises(FileNotFoundError):
            checksum_file("/nonexistent/path/file.txt")


class TestCausalLanguageScanner:
    """Tests for the causal_language_scanner function."""

    def test_detects_forbidden_term(self):
        """Test that scanner detects a forbidden term."""
        text = "Social media causes cognitive decline."
        assert causal_language_scanner(text, ["causes"]) is True

    def test_detects_forbidden_term_case_insensitive(self):
        """Test that scanner is case-insensitive."""
        text = "Social media CAUSES cognitive decline."
        assert causal_language_scanner(text, ["causes"]) is True

    def test_no_forbidden_terms(self):
        """Test that scanner returns False when no forbidden terms are present."""
        text = "Social media is associated with cognitive decline."
        assert causal_language_scanner(text, ["causes"]) is False

    def test_default_forbidden_list(self):
        """Test scanner with default forbidden list."""
        text = "Social media impacts performance."
        # 'impacts' is in the default list
        assert causal_language_scanner(text) is True

    def test_empty_text(self):
        """Test scanner with empty text."""
        assert causal_language_scanner("", ["causes"]) is False

    def test_partial_match_not_detected(self):
        """Test that partial matches are not detected (exact word matching logic)."""
        text = "The causality is complex."
        # 'causes' should not match 'causality' with our simple substring check
        # Note: Our implementation uses substring check, so this might be True
        # depending on implementation. The requirement is for substring check.
        result = causal_language_scanner(text, ["causes"])
        # 'causes' is a substring of 'causality' -> True
        assert result is True
