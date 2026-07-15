import pytest
import sys
import time
from unittest.mock import patch
from main import check_runtime_limit

class TestRuntimeTimeout:
    """Tests for the runtime timeout logic (T016b)."""

    def test_no_abort_within_limit(self):
        """Test that no abort occurs when within the 6-hour limit."""
        start_time = time.time()
        # Should not raise
        check_runtime_limit(start_time)

    def test_abort_exceeds_limit(self):
        """Test that sys.exit is called with the correct message when limit exceeded."""
        # Simulate a start time 7 hours ago
        start_time = time.time() - (7 * 60 * 60)
        
        expected_msg = "Runtime ceiling (6h) exceeded. Aborting grid."
        
        with patch('sys.exit') as mock_exit:
            check_runtime_limit(start_time)
            mock_exit.assert_called_once_with(expected_msg)

    def test_abort_message_content(self):
        """Verify the exact message passed to sys.exit."""
        start_time = time.time() - (7 * 60 * 60)
        
        with patch('sys.exit') as mock_exit:
            check_runtime_limit(start_time)
            # Check the argument passed to sys.exit
            call_args = mock_exit.call_args
            assert call_args[0][0] == "Runtime ceiling (6h) exceeded. Aborting grid."