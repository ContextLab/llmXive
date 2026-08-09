"""
Unit tests for the logging infrastructure and exclusion rate tracking.
"""

import logging
import pytest
import os
from pathlib import Path
import tempfile

from code.utils.logger import (
    setup_logging,
    get_logger,
    increment_exclusion,
    increment_processed,
    get_exclusion_rate,
    reset_counters,
    log_exclusion_summary
)


class TestExclusionTracking:
    """Tests for the exclusion rate tracking logic."""

    def setup_method(self):
        """Reset counters before each test."""
        reset_counters()

    def test_initial_state(self):
        """Verify counters start at zero."""
        assert get_exclusion_rate() == 0.0

    def test_increment_processed(self):
        """Test that processed count increases."""
        increment_processed()
        increment_processed()
        # Rate should still be 0.0 as no exclusions
        assert get_exclusion_rate() == 0.0

    def test_increment_exclusion(self):
        """Test that exclusion count increases."""
        increment_processed()
        increment_exclusion("cloud")
        assert get_exclusion_rate() == 0.5

    def test_multiple_reasons(self):
        """Test tracking exclusions by specific reason."""
        increment_processed()
        increment_processed()
        increment_processed()

        increment_exclusion("cloud")
        increment_exclusion("cloud")
        increment_exclusion("missing_label")

        rate = get_exclusion_rate()
        assert rate == 1.0  # 2 exclusions out of 3 processed? No, 3 processed, 3 excluded?
        # Wait: 3 processed, 3 excluded (2 cloud + 1 label) -> 100%
        # Let's re-verify logic:
        # 3 processed
        # 3 excluded
        # Rate = 3/3 = 1.0

        # Let's test a partial rate
        reset_counters()
        increment_processed()
        increment_processed()
        increment_processed()
        increment_processed()

        increment_exclusion("cloud") # 1/4 = 0.25
        assert get_exclusion_rate() == 0.25

    def test_reset_counters(self):
        """Test that resetting counters clears state."""
        increment_processed()
        increment_exclusion("test")
        reset_counters()
        assert get_exclusion_rate() == 0.0

class TestLoggingSetup:
    """Tests for the logging configuration."""

    def test_console_handler_exists(self):
        """Verify that a console handler is created."""
        logger = setup_logging(log_level="INFO")
        # Check root logger
        root = logging.getLogger()
        handlers = [h for h in root.handlers if isinstance(h, logging.StreamHandler)]
        assert len(handlers) >= 1

    def test_file_handler_creation(self):
        """Verify that a file handler is created when a path is provided."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test.log"
            setup_logging(log_level="INFO", log_file=str(log_path))

            root = logging.getLogger()
            file_handlers = [h for h in root.handlers if isinstance(h, logging.FileHandler)]
            assert len(file_handlers) >= 1
            assert log_path.exists()

    def test_log_level_respected(self):
        """Verify that the log level is set correctly."""
        setup_logging(log_level="WARNING")
        root = logging.getLogger()
        assert root.level == logging.WARNING

    def test_get_logger(self):
        """Verify that get_logger returns a valid logger."""
        logger = get_logger("test_module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_module"

class TestExclusionSummary:
    """Tests for the exclusion summary logging."""

    def setup_method(self):
        reset_counters()
        # Setup a logger with a StringHandler to capture output
        self.logger = logging.getLogger("test_summary")
        self.logger.handlers.clear()
        self.logger.setLevel(logging.INFO)
        self.handler = logging.StreamHandler()
        self.handler.setLevel(logging.INFO)
        self.logger.addHandler(self.handler)

    def test_summary_logs_correctly(self):
        """Verify that the summary logs the correct counts."""
        increment_processed()
        increment_processed()
        increment_exclusion("cloud")

        # Capture logs
        import io
        import contextlib

        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            log_exclusion_summary(self.logger)

        output = f.getvalue()
        assert "Exclusion Summary" in output
        assert "1/2" in output
        assert "cloud" in output