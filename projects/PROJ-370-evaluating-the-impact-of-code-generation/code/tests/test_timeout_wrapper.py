"""
Tests for the timeout wrapper functionality.
"""
import os
import sys
import time
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from code.src.utils.timeout_wrapper import (
    set_global_timeout,
    check_timeout,
    setup_timeout_logging,
    TimeoutContext,
    enforce_timeout,
    EXIT_CODE_TIMEOUT,
    DEFAULT_TIMEOUT_HOURS
)

class TestTimeoutWrapper:
    """Test cases for timeout wrapper functionality."""

    @pytest.fixture(autouse=True)
    def reset_timeout_state(self):
        """Reset global timeout state before each test."""
        # Import here to avoid circular imports
        from code.src.utils import timeout_wrapper
        timeout_wrapper._start_time = None
        timeout_wrapper._timeout_seconds = DEFAULT_TIMEOUT_HOURS * 3600
        yield
        # Reset after test
        timeout_wrapper._start_time = None
        timeout_wrapper._timeout_seconds = DEFAULT_TIMEOUT_HOURS * 3600

    def test_set_global_timeout(self):
        """Test setting global timeout duration."""
        set_global_timeout(2.5)  # 2.5 hours
        from code.src.utils import timeout_wrapper
        assert timeout_wrapper._timeout_seconds == int(2.5 * 3600)
        assert timeout_wrapper._start_time is None

    def test_check_timeout_before_start(self):
        """Test that timeout check returns False before start time is set."""
        assert check_timeout() is False

    def test_check_timeout_within_limit(self):
        """Test timeout check when within limit."""
        set_global_timeout(1)  # 1 hour
        from code.src.utils import timeout_wrapper
        timeout_wrapper._start_time = time.time() - 300  # 5 minutes ago
        assert check_timeout() is False

    def test_check_timeout_exceeded(self):
        """Test timeout check when limit is exceeded."""
        set_global_timeout(0.001)  # 3.6 seconds
        from code.src.utils import timeout_wrapper
        timeout_wrapper._start_time = time.time() - 10  # 10 seconds ago
        
        # Create a temporary logger to avoid file I/O in test
        with patch('code.src.utils.timeout_wrapper.setup_timeout_logging') as mock_logger:
            mock_logger.return_value = MagicMock()
            result = check_timeout()
            assert result is True
            mock_logger.return_value.warning.assert_called_once()

    def test_timeout_context_manager(self):
        """Test TimeoutContext as a context manager."""
        from code.src.utils import timeout_wrapper
        timeout_wrapper._start_time = time.time()
        
        # Should not raise within timeout
        with TimeoutContext(hours=1):
            pass

    def test_timeout_context_exceeded(self):
        """Test TimeoutContext when timeout is exceeded."""
        set_global_timeout(0.0001)  # Very short timeout
        from code.src.utils import timeout_wrapper
        timeout_wrapper._start_time = time.time() - 10  # Already exceeded
        
        # Mock sys.exit to prevent actual exit
        with patch('sys.exit') as mock_exit:
            with patch('code.src.utils.timeout_wrapper.setup_timeout_logging') as mock_logger:
                mock_logger.return_value = MagicMock()
                try:
                    with TimeoutContext(hours=0.0001):
                        pass
                except SystemExit:
                    pass
                
                # Verify exit was called with correct code
                mock_exit.assert_called_with(EXIT_CODE_TIMEOUT)

    def test_enforce_timeout_decorator(self):
        """Test enforce_timeout decorator."""
        @enforce_timeout(hours=1)
        def test_function():
            return "success"
        
        result = test_function()
        assert result == "success"

    def test_setup_timeout_logging_creates_file(self):
        """Test that setup_timeout_logging creates the log file."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = setup_timeout_logging(log_dir=tmpdir)
            log_path = Path(tmpdir) / "timeout.log"
            assert log_path.exists() or len(logger.handlers) > 0

    def test_timeout_logging_content(self):
        """Test that timeout logging writes correct content."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = setup_timeout_logging(log_dir=tmpdir)
            logger.warning("Test timeout message")
            
            log_path = Path(tmpdir) / "timeout.log"
            assert log_path.exists()
            
            content = log_path.read_text()
            assert "Test timeout message" in content