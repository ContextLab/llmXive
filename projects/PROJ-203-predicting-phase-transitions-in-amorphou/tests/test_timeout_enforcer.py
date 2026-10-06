"""
Unit tests for the PipelineTimeout context manager.
"""
import time
import pytest
from unittest.mock import patch
from code.utils.timeout_enforcer import TimeoutEnforcer, PipelineTimeout


class TestTimeoutEnforcer:
    """Tests for the TimeoutEnforcer class."""

    def test_within_time_limit(self, tmp_path):
        """Test that no exception is raised when execution is within the limit."""
        log_path = tmp_path / "timeout.log"
        with TimeoutEnforcer(max_seconds=10.0, log_path=str(log_path)):
            time.sleep(0.1)
        # Should not raise
        assert not log_path.exists() or log_path.stat().st_size == 0

    def test_exceeds_time_limit(self, tmp_path):
        """Test that TimeoutError is raised when execution exceeds the limit."""
        log_path = tmp_path / "timeout.log"
        with pytest.raises(TimeoutError):
            with TimeoutEnforcer(max_seconds=0.1, log_path=str(log_path)):
                time.sleep(0.2)
        
        # Verify log was written
        assert log_path.exists()
        with open(log_path, 'r') as f:
            content = f.read()
            assert "TIMEOUT" in content

    def test_no_log_path(self, tmp_path):
        """Test that TimeoutError is raised even without a log path."""
        with pytest.raises(TimeoutError):
            with TimeoutEnforcer(max_seconds=0.05):
                time.sleep(0.1)

    def test_context_manager_entry_exit(self, tmp_path):
        """Test that the context manager properly initializes and cleans up."""
        log_path = tmp_path / "timeout.log"
        enforcer = TimeoutEnforcer(max_seconds=10.0, log_path=str(log_path))
        
        with enforcer:
            assert enforcer.start_time is not None
            assert enforcer.elapsed_time == 0.0
        
        assert enforcer.elapsed_time > 0.0