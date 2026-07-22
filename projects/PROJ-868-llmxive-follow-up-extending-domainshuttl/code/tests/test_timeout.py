"""
Tests for the timeout utility (T017).
"""

import json
import os
import time
from pathlib import Path
import pytest

from src.utils.timeout import with_timeout, _log_timeout, LOG_FILE, LOG_DIR


class TestTimeoutWrapper:
    """Tests for the with_timeout decorator."""

    def test_function_completes_within_timeout(self):
        """Test that a fast function executes normally."""
        @with_timeout(timeout_seconds=5.0, sample_id="test_fast")
        def fast_func():
            return "success"

        result = fast_func()
        assert result == "success"

    def test_function_times_out(self):
        """Test that a slow function triggers the timeout handler."""
        @with_timeout(timeout_seconds=0.5, sample_id="test_slow")
        def slow_func():
            time.sleep(2.0)
            return "should_not_reach"

        result = slow_func()
        # The wrapper should return None on timeout
        assert result is None

    def test_timeout_log_created(self):
        """Test that the timeout log file is created and updated."""
        # Ensure log file doesn't exist initially for a clean test
        if LOG_FILE.exists():
            LOG_FILE.unlink()

        sample_id = f"test_log_{time.time()}"

        @with_timeout(timeout_seconds=0.1, sample_id=sample_id)
        def always_times_out():
            time.sleep(5.0)

        always_times_out()

        assert LOG_FILE.exists(), "Log file should be created on timeout."

        with open(LOG_FILE, "r", encoding="utf-8") as f:
            logs = json.load(f)

        assert len(logs) >= 1
        last_entry = logs[-1]
        assert last_entry["sample_id"] == sample_id
        assert "duration_seconds" in last_entry
        assert last_entry["function"] == "always_times_out"

    def test_exception_propagation(self):
        """Test that non-timeout exceptions are re-raised."""
        @with_timeout(timeout_seconds=5.0, sample_id="test_error")
        def raising_func():
            raise ValueError("Intentional error")

        with pytest.raises(ValueError, match="Intentional error"):
            raising_func()

def test_log_timeout_direct():
    """Test the internal logging function directly."""
    sample_id = "direct_log_test"
    _log_timeout(sample_id, 1.5, "test_func")

    assert LOG_FILE.exists()
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        logs = json.load(f)

    # Find the entry we just added
    found = False
    for entry in logs:
        if entry["sample_id"] == sample_id and entry["function"] == "test_func":
            found = True
            assert entry["duration_seconds"] == 1.5
            break

    assert found, "Direct log entry not found in file."