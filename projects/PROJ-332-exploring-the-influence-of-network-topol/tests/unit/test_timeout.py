import pytest
import sys
import time
from unittest.mock import patch, MagicMock
import os

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from main import check_runtime_limit, abort_on_timeout

class TestTimeoutLogic:
    """Tests for runtime timeout and abort logic (T016b)."""

    def test_check_runtime_limit_not_exceeded(self):
        """Test that check_runtime_limit returns False when time is within limit."""
        # Reset global timer
        import main
        main._GLOBAL_START_TIME = time.time()
        
        # Check immediately
        result = check_runtime_limit()
        assert result is False

    def test_check_runtime_limit_exceeded(self):
        """Test that check_runtime_limit returns True when time exceeds 6 hours."""
        import main
        # Set start time to 7 hours ago
        main._GLOBAL_START_TIME = time.time() - (7 * 60 * 60)
        
        result = check_runtime_limit()
        assert result is True

    @patch('sys.exit')
    def test_abort_on_timeout_exits_with_message(self, mock_exit):
        """Test that abort_on_timeout calls sys.exit(1) with the correct message when limit exceeded."""
        import main
        # Set start time to 7 hours ago
        main._GLOBAL_START_TIME = time.time() - (7 * 60 * 60)
        
        # Mock logger to capture the message
        with patch('main.logger') as mock_logger:
            # This should trigger the exit
            with pytest.raises(SystemExit) as exc_info:
                abort_on_timeout()
            
            # Verify sys.exit was called with 1
            mock_exit.assert_called_once_with(1)
            # Verify the error message was logged
            mock_logger.error.assert_called_once_with("Runtime ceiling (6h) exceeded. Aborting grid.")
            assert exc_info.value.code == 1

    @patch('sys.exit')
    def test_abort_on_timeout_no_exit_when_ok(self, mock_exit):
        """Test that abort_on_timeout does not exit when time is within limit."""
        import main
        # Reset timer
        main._GLOBAL_START_TIME = time.time()
        
        # This should not exit
        abort_on_timeout()
        
        mock_exit.assert_not_called()
