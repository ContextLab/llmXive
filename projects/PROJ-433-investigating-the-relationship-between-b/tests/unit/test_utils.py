"""
Unit tests for code/utils.py QC functions (T004c).
"""
import logging
import os
import tempfile
from pathlib import Path
import pytest

# Import the functions under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
from utils import check_fd, log_exclusion, setup_logger


class TestCheckFD:
    def test_fd_below_threshold_returns_true(self):
        """FD 0.3 should pass with default threshold 0.5."""
        assert check_fd(0.3) is True

    def test_fd_at_threshold_returns_true(self):
        """FD exactly 0.5 should pass with default threshold 0.5."""
        assert check_fd(0.5) is True

    def test_fd_above_threshold_returns_false(self):
        """FD 0.6 should fail with default threshold 0.5."""
        assert check_fd(0.6) is False

    def test_custom_threshold(self):
        """Custom threshold 0.2 should reject 0.3."""
        assert check_fd(0.3, threshold=0.2) is False
        assert check_fd(0.1, threshold=0.2) is True


class TestLogExclusion:
    def test_log_exclusion_writes_to_handler(self, tmp_path):
        """Verify log_exclusion writes the expected formatted string."""
        # Setup a temporary logger for the test
        log_file = tmp_path / "test_log.txt"
        logger = logging.getLogger("test_qc")
        logger.setLevel(logging.DEBUG)
        
        # Clear existing handlers to avoid interference
        logger.handlers.clear()
        
        handler = logging.FileHandler(log_file)
        formatter = logging.Formatter("%(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        subject_id = "sub-001"
        reason = "FD > 0.5mm"
        
        log_exclusion(logger, reason, subject_id)
        
        # Flush handlers to ensure write
        logger.handlers[0].flush()
        
        content = log_file.read_text()
        assert f"EXCLUSION | Subject: {subject_id} | Reason: {reason}" in content

    def test_log_exclusion_format(self):
        """Verify the exact log format string."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_path = Path(tmp_dir) / "format_test.log"
            logger = logging.getLogger("format_test")
            logger.handlers.clear()
            handler = logging.FileHandler(log_path)
            logger.addHandler(handler)
            
            log_exclusion(logger, "Motion Spike", "sub-999")
            handler.flush()
            
            content = log_path.read_text()
            expected = "EXCLUSION | Subject: sub-999 | Reason: Motion Spike"
            assert expected in content