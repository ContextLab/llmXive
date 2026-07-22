"""
Tests for the timeout utility module.
"""

import json
import os
import time
from pathlib import Path
import pytest
from src.utils.timeout import with_timeout, _log_timeout, LOG_FILE, LOG_DIR, TimeoutError


class TestTimeoutWrapper:
    """Tests for the with_timeout decorator and timeout_wrapper function."""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path, monkeypatch):
        """Setup temporary directories and reset log state for each test."""
        self.tmp_dir = tmp_path
        self.log_dir = self.tmp_dir / "data" / "processed"
        self.log_file = self.log_dir / "timeout_log.json"
        
        # Monkeypatch the global log paths
        monkeypatch.setattr("src.utils.timeout.LOG_DIR", self.log_dir)
        monkeypatch.setattr("src.utils.timeout.LOG_FILE", self.log_file)
        
        # Ensure directory exists
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def test_successful_execution(self):
        """Test that a function completing within the timeout runs successfully."""
        timeout_seconds = 2
        
        @with_timeout(timeout_seconds)
        def quick_function(sample_id):
            return "success"

        result = quick_function("test_123")
        assert result == "success"
        assert not self.log_file.exists()

    def test_timeout_execution(self):
        """Test that a function exceeding the timeout is caught and logged."""
        timeout_seconds = 1
        
        @with_timeout(timeout_seconds)
        def slow_function(sample_id):
            time.sleep(3)
            return "should_not_reach"

        result = slow_function("test_slow")
        
        # Should return None (sentinel)
        assert result is None
        
        # Should log the timeout
        assert self.log_file.exists()
        
        with open(self.log_file, "r") as f:
            logs = json.load(f)
        
        assert len(logs) == 1
        assert logs[0]["sample_id"] == "test_slow"
        assert "timed out" in logs[0]["error_message"]
        assert logs[0]["duration_seconds"] >= timeout_seconds

    def test_timeout_wrapper_function(self):
        """Test the imperative timeout_wrapper function."""
        timeout_seconds = 1
        
        def slow_func(sample_id):
            time.sleep(2)
            return "fail"

        wrapped = timeout_wrapper(slow_func, timeout_seconds, "test_wrapper")
        result = wrapped()

        assert result is None
        assert self.log_file.exists()

    def test_multiple_samples(self):
        """Test logging multiple timeout events."""
        timeout_seconds = 1
        
        @with_timeout(timeout_seconds)
        def slow_func(sample_id):
            time.sleep(2)
            return "fail"

        slow_func("sample_A")
        slow_func("sample_B")

        with open(self.log_file, "r") as f:
            logs = json.load(f)

        assert len(logs) == 2
        sample_ids = {log["sample_id"] for log in logs}
        assert "sample_A" in sample_ids
        assert "sample_B" in sample_ids


def test_log_timeout_direct(tmp_path, monkeypatch):
    """Test the internal logging function directly."""
    log_dir = tmp_path / "logs"
    log_file = log_dir / "test_log.json"
    
    monkeypatch.setattr("src.utils.timeout.LOG_DIR", log_dir)
    monkeypatch.setattr("src.utils.timeout.LOG_FILE", log_file)
    
    log_dir.mkdir(parents=True, exist_ok=True)

    _log_timeout("direct_test", 1.5, "Test error message")

    assert log_file.exists()
    with open(log_file, "r") as f:
        data = json.load(f)

    assert len(data) == 1
    assert data[0]["sample_id"] == "direct_test"
    assert data[0]["duration_seconds"] == 1.5
    assert data[0]["error_message"] == "Test error message"
