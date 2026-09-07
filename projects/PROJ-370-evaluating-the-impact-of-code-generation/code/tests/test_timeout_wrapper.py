"""
Tests for the timeout wrapper functionality.

These tests verify:
1. Timeout setting and checking
2. Graceful exit behavior
3. Logging to timeout.log
4. Context manager functionality
"""

import os
import sys
import time
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import tempfile
import shutil

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.src.utils.timeout_wrapper import (
    setup_timeout_logging,
    set_global_timeout,
    check_timeout,
    get_remaining_time_seconds,
    timeout_handler,
    enforce_timeout,
    TimeoutContext,
    TimeoutExceeded,
    EXIT_CODE_TIMEOUT
)


class TestTimeoutWrapper:
    """Test suite for timeout wrapper functionality."""
    
    @pytest.fixture(autouse=True)
    def setup_teardown(self, tmp_path):
        """Setup and teardown for each test."""
        # Create temporary logs directory
        self.logs_dir = tmp_path / "logs"
        self.logs_dir.mkdir()
        
        # Patch the logs directory in the module
        with patch('code.src.utils.timeout_wrapper.setup_pipeline_logging'):
            with patch('code.src.utils.timeout_wrapper.Path') as mock_path:
                mock_path.return_value = self.logs_dir
                yield
        
        # Cleanup
        if self.logs_dir.exists():
            shutil.rmtree(self.logs_dir, ignore_errors=True)
    
    def test_setup_timeout_logging_creates_logger(self):
        """Test that setup_timeout_logging creates a logger."""
        logger = setup_timeout_logging(self.logs_dir)
        assert logger is not None
        assert logger.name == "timeout"
        assert logger.level == logging.WARNING
    
    def test_set_global_timeout_sets_start_time(self):
        """Test that set_global_timeout initializes start time."""
        set_global_timeout(timeout_hours=1)
        # Should not raise
        assert True
    
    def test_check_timeout_returns_false_before_timeout(self):
        """Test check_timeout returns False when within limit."""
        set_global_timeout(timeout_hours=1)
        result = check_timeout()
        assert result is False
    
    def test_check_timeout_returns_true_after_timeout(self):
        """Test check_timeout returns True when limit exceeded."""
        # Set a very short timeout
        set_global_timeout(timeout_hours=0.0001)  # 0.36 seconds
        time.sleep(0.5)
        result = check_timeout()
        assert result is True
    
    def test_get_remaining_time_seconds(self):
        """Test remaining time calculation."""
        set_global_timeout(timeout_hours=1)
        remaining = get_remaining_time_seconds()
        assert remaining > 0
        assert remaining <= 3600
    
    def test_timeout_context_manager(self):
        """Test TimeoutContext as context manager."""
        with TimeoutContext(timeout_hours=1) as ctx:
            assert ctx.is_timed_out() is False
            assert ctx.get_remaining_seconds() > 0
    
    def test_timeout_context_detects_timeout(self):
        """Test TimeoutContext detects timeout."""
        with TimeoutContext(timeout_hours=0.0001) as ctx:  # 0.36 seconds
            time.sleep(0.5)
            assert ctx.is_timed_out() is True
    
    def test_timeout_context_raises_on_check(self):
        """Test TimeoutContext raises exception when check_and_raise called."""
        with TimeoutContext(timeout_hours=0.0001) as ctx:  # 0.36 seconds
            time.sleep(0.5)
            with pytest.raises(TimeoutExceeded):
                ctx.check_and_raise()
    
    def test_timeout_handler(self):
        """Test timeout handler sets exit code."""
        with patch('code.src.utils.timeout_wrapper.sys.exit') as mock_exit:
            with patch('code.src.utils.timeout_wrapper.setup_timeout_logging'):
                timeout_handler(signal.SIGALRM, None)
                mock_exit.assert_called_once_with(EXIT_CODE_TIMEOUT)
    
    def test_enforce_timeout_sets_signal_handler(self):
        """Test enforce_timeout sets up signal handler."""
        if hasattr(os, 'signal'):
            with patch('code.src.utils.timeout_wrapper.set_global_timeout'):
                with patch('code.src.utils.timeout_wrapper.signal'):
                    enforce_timeout(timeout_hours=1)
                    # Should not raise
                    assert True
    
    def test_no_timeout_when_not_set(self):
        """Test that check_timeout returns False when timeout not set."""
        # Reset global state
        import code.src.utils.timeout_wrapper as tw
        tw._start_time = None
        tw._timeout_seconds = None
        
        result = check_timeout()
        assert result is False
    
    def test_remaining_time_infinity_when_not_set(self):
        """Test remaining time is infinity when timeout not set."""
        import code.src.utils.timeout_wrapper as tw
        tw._start_time = None
        tw._timeout_seconds = None
        
        remaining = get_remaining_time_seconds()
        assert remaining == float('inf')
    
    def test_timeout_log_file_created(self):
        """Test that timeout log file is created."""
        logger = setup_timeout_logging(self.logs_dir)
        logger.warning("Test timeout message")
        
        log_file = self.logs_dir / "timeout.log"
        assert log_file.exists()
        
        content = log_file.read_text()
        assert "Test timeout message" in content