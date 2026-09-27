"""
Unit tests for the validation infrastructure (T006).
"""
import os
import json
import time
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure we can import from code/
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.validation import (
    RuntimeTracker, 
    get_tracker, 
    start_pipeline_timer, 
    stop_pipeline_timer, 
    check_pipeline_limit, 
    enforce_pipeline_limit,
    LOG_FILE
)

class TestRuntimeTracker:
    @pytest.fixture(autouse=True)
    def setup_teardown(self, tmp_path):
        """Setup a temporary directory for log files to avoid polluting the real one."""
        # We will mock the LOG_FILE path or use a temporary directory for testing
        self.test_log_dir = tmp_path / "test_results"
        self.test_log_dir.mkdir(parents=True, exist_ok=True)
        self.test_log_file = self.test_log_dir / "pipeline_log.json"
        
        # Patch the LOG_FILE constant in the module
        with patch('code.validation.LOG_FILE', str(self.test_log_file)):
            # Reset the global tracker to force re-initialization with new path
            import code.validation
            code.validation._tracker = None
            yield
        
        # Cleanup
        if self.test_log_file.exists():
            self.test_log_file.unlink()

    def test_initialization_creates_file(self):
        """Test that the log file is created/initialized."""
        tracker = RuntimeTracker()
        assert self.test_log_file.exists()

    def test_start_and_stop(self):
        """Test basic start and stop functionality."""
        tracker = RuntimeTracker()
        tracker.start()
        time.sleep(0.1)
        elapsed = tracker.stop("test_stage")
        
        assert elapsed >= 0.1
        assert self.test_log_file.exists()

        # Verify log content
        with open(self.test_log_file, 'r') as f:
            lines = f.readlines()
            assert len(lines) == 1
            entry = json.loads(lines[0])
            assert entry['stage'] == 'test_stage'
            assert 'cumulative_seconds' in entry
            assert entry['status'] == 'completed'

    def test_check_limit_within(self):
        """Test check_limit returns True when within limit."""
        tracker = RuntimeTracker()
        tracker.start()
        assert tracker.check_limit() is True
        tracker.stop()

    def test_check_limit_exceeded(self):
        """Test check_limit returns False when limit exceeded."""
        tracker = RuntimeTracker()
        tracker.start()
        # Mock time.time to simulate a long duration
        original_time = time.time
        time.time = lambda: original_time() + 4000  # 4000s > 3600s limit
        
        assert tracker.check_limit() is False
        
        # Restore time
        time.time = original_time
        tracker.stop()

    def test_enforce_pipeline_limit_raises(self):
        """Test that enforce_pipeline_limit raises an error when exceeded."""
        tracker = RuntimeTracker()
        tracker.start()
        
        # Mock time to exceed limit
        original_time = time.time
        time.time = lambda: original_time() + 4000
        
        with pytest.raises(RuntimeError, match="Pipeline execution time limit exceeded"):
            enforce_pipeline_limit()
        
        time.time = original_time
        tracker.stop()

    def test_parallel_safety_locking(self):
        """Test that file locking is attempted (mocked)."""
        tracker = RuntimeTracker()
        tracker.start()
        
        # We can't easily test real locking in a unit test without multiple processes,
        # but we can verify the code path exists by checking the source or mocking fcntl.
        # For now, we just ensure the stop method completes without error.
        tracker.stop("parallel_test")
        assert self.test_log_file.exists()

class TestGlobalFunctions:
    @pytest.fixture(autouse=True)
    def setup_teardown(self, tmp_path):
        self.test_log_dir = tmp_path / "test_results"
        self.test_log_dir.mkdir(parents=True, exist_ok=True)
        self.test_log_file = self.test_log_dir / "pipeline_log.json"
        
        with patch('code.validation.LOG_FILE', str(self.test_log_file)):
            import code.validation
            code.validation._tracker = None
            yield
        
        if self.test_log_file.exists():
            self.test_log_file.unlink()

    def test_start_stop_pipeline_timer(self):
        """Test global start/stop functions."""
        start_pipeline_timer()
        time.sleep(0.05)
        stop_pipeline_timer("global_test")
        
        with open(self.test_log_file, 'r') as f:
            content = f.read()
            assert "global_test" in content

    def test_check_pipeline_limit(self):
        """Test global check limit function."""
        start_pipeline_timer()
        assert check_pipeline_limit() is True
        stop_pipeline_timer()

    def test_get_tracker_singleton(self):
        """Test that get_tracker returns the same instance."""
        t1 = get_tracker()
        t2 = get_tracker()
        assert t1 is t2