"""
Unit tests for timeout_wrapper module.

Tests cover:
1. Timeout initialization
2. Timeout checking
3. Timeout handling
4. Context manager usage
"""

import os
import sys
import time
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.timeout_wrapper import (
    setup_timeout_logging,
    set_global_timeout,
    check_timeout,
    timeout_handler,
    enforce_timeout,
    TimeoutContext,
    GLOBAL_TIMEOUT_SECONDS,
    TIMEOUT_LOG_FILE
)


class TestTimeoutWrapper:
    """Test suite for timeout wrapper functionality."""
    
    def setup_method(self):
        """Set up test fixtures before each test."""
        # Reset global state before each test
        import src.utils.timeout_wrapper as tw
        tw._start_time = None
        tw._timeout_handler_installed = False
        tw._logger = None
        
        # Ensure logs directory exists
        logs_dir = "logs"
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)
        
        # Clean up timeout log if it exists
        timeout_log = Path(TIMEOUT_LOG_FILE)
        if timeout_log.exists():
            timeout_log.unlink()
    
    def teardown_method(self):
        """Clean up after each test."""
        # Remove timeout log if it exists
        timeout_log = Path(TIMEOUT_LOG_FILE)
        if timeout_log.exists():
            timeout_log.unlink()
    
    def test_setup_timeout_logging_creates_logger(self):
        """Test that setup_timeout_logging creates and returns a logger."""
        logger = setup_timeout_logging()
        
        assert logger is not None
        assert isinstance(logger, logging.Logger)
        assert logger.name == "timeout"
        assert logger.level == logging.WARNING
        assert len(logger.handlers) > 0
    
    def test_setup_timeout_logging_creates_log_file(self):
        """Test that setup_timeout_logging creates the log file."""
        logger = setup_timeout_logging()
        
        timeout_log = Path(TIMEOUT_LOG_FILE)
        assert timeout_log.exists()
    
    def test_set_global_timeout_sets_start_time(self):
        """Test that set_global_timeout sets the start time."""
        set_global_timeout()
        
        import src.utils.timeout_wrapper as tw
        assert tw._start_time is not None
        assert tw._start_time > 0
    
    def test_check_timeout_returns_false_when_not_exceeded(self):
        """Test that check_timeout returns False when timeout not exceeded."""
        set_global_timeout()
        
        # Immediately check - should not be exceeded
        assert check_timeout() is False
    
    def test_check_timeout_returns_true_when_exceeded(self):
        """Test that check_timeout returns True when timeout is exceeded."""
        import src.utils.timeout_wrapper as tw
        
        # Manually set start time to 7 hours ago
        tw._start_time = time.time() - (7 * 60 * 60)
        
        assert check_timeout() is True
    
    def test_timeout_handler_logs_warning_and_exits(self):
        """Test that timeout_handler logs warning and exits with code 143."""
        import src.utils.timeout_wrapper as tw
        
        # Set start time to ensure timeout is exceeded
        tw._start_time = time.time() - (7 * 60 * 60)
        
        with patch('sys.exit') as mock_exit:
            timeout_handler(0, None)
            
            mock_exit.assert_called_once_with(143)
    
    def test_timeout_handler_logs_to_file(self):
        """Test that timeout_handler logs to the timeout log file."""
        import src.utils.timeout_wrapper as tw
        
        # Set start time to ensure timeout is exceeded
        tw._start_time = time.time() - (7 * 60 * 60)
        
        # Call timeout handler (but don't actually exit)
        with patch('sys.exit'):
            timeout_handler(0, None)
        
        # Check log file content
        timeout_log = Path(TIMEOUT_LOG_FILE)
        assert timeout_log.exists()
        
        content = timeout_log.read_text()
        assert "TIMEOUT EXCEEDED" in content
        assert "Skipping remaining PRs" in content
    
    def test_enforce_timeout_sets_up_handler(self):
        """Test that enforce_timeout sets up the timeout handler."""
        with patch('signal.signal') as mock_signal:
            with patch('signal.alarm') as mock_alarm:
                enforce_timeout()
                
                # Should set up signal handler
                mock_signal.assert_called_once()
                # Should set alarm
                mock_alarm.assert_called_once()
    
    def test_timeout_context_manager(self):
        """Test that TimeoutContext context manager works correctly."""
        context = TimeoutContext()
        
        with context:
            # Should be able to use the context
            assert context.is_timeout_reached() is False
    
    def test_timeout_context_manager_detects_timeout(self):
        """Test that TimeoutContext detects when timeout is exceeded."""
        import src.utils.timeout_wrapper as tw
        
        # Set start time to ensure timeout is exceeded
        tw._start_time = time.time() - (7 * 60 * 60)
        
        context = TimeoutContext()
        
        with context:
            assert context.is_timeout_reached() is True
    
    def test_check_timeout_without_initialization(self):
        """Test that check_timeout returns False when timeout not initialized."""
        import src.utils.timeout_wrapper as tw
        
        # Reset start time
        tw._start_time = None
        
        assert check_timeout() is False
    
    def test_multiple_set_global_timeout_calls(self):
        """Test that multiple calls to set_global_timeout work correctly."""
        set_global_timeout()
        first_time = time.time()
        
        time.sleep(0.1)
        set_global_timeout()
        second_time = time.time()
        
        import src.utils.timeout_wrapper as tw
        assert tw._start_time >= first_time
        assert tw._start_time <= second_time
    
    def test_global_timeout_constant(self):
        """Test that GLOBAL_TIMEOUT_SECONDS is correctly set to 6 hours."""
        assert GLOBAL_TIMEOUT_SECONDS == 6 * 60 * 60
    
    def test_timeout_log_file_path(self):
        """Test that TIMEOUT_LOG_FILE is correctly set."""
        assert TIMEOUT_LOG_FILE == "logs/timeout.log"
    
    def test_enforce_timeout_ignores_second_call(self):
        """Test that enforce_timeout is idempotent."""
        with patch('signal.signal') as mock_signal:
            with patch('signal.alarm') as mock_alarm:
                enforce_timeout()
                first_call_count = mock_signal.call_count
                
                enforce_timeout()
                second_call_count = mock_signal.call_count
                
                # Should only be called once
                assert first_call_count == second_call_count
    
    def test_timeout_handler_with_start_time(self):
        """Test timeout_handler logs runtime stats when start time is set."""
        import src.utils.timeout_wrapper as tw
        
        # Set start time
        tw._start_time = time.time() - 100  # 100 seconds ago
        
        with patch('sys.exit'):
            timeout_handler(0, None)
        
        # Check log file for runtime stats
        timeout_log = Path(TIMEOUT_LOG_FILE)
        content = timeout_log.read_text()
        assert "Total runtime" in content
    
    def test_timeout_handler_without_start_time(self):
        """Test timeout_handler works even when start time is not set."""
        import src.utils.timeout_wrapper as tw
        
        # Reset start time
        tw._start_time = None
        
        with patch('sys.exit'):
            # Should not raise an exception
            timeout_handler(0, None)
    
    def test_main_function(self):
        """Test that main function runs without errors."""
        from src.utils.timeout_wrapper import main
        
        with patch('src.utils.timeout_wrapper.check_timeout', return_value=False):
            with patch('src.utils.timeout_wrapper.logger'):
                # Should complete without errors
                main()
    
    def test_is_timeout_reached_with_actual_timeout(self):
        """Test is_timeout_reached with actual timeout condition."""
        import src.utils.timeout_wrapper as tw
        
        # Set start time to 7 hours ago
        tw._start_time = time.time() - (7 * 60 * 60)
        
        context = TimeoutContext()
        assert context.is_timeout_reached() is True
    
    def test_is_timeout_reached_without_timeout(self):
        """Test is_timeout_reached without timeout condition."""
        import src.utils.timeout_wrapper as tw
        
        # Set start time to now
        tw._start_time = time.time()
        
        context = TimeoutContext()
        assert context.is_timeout_reached() is False