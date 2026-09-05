import unittest
import sys
import os
import tempfile
import logging
from unittest.mock import patch, MagicMock
import responses

# Ensure the project root is in the path to allow imports from code/
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from data.fetch_gdelt import main as main_gdelt
from data.fetch_google_trends import main as main_trends
from utils.logging import get_logger

class TestErrorHandling(unittest.TestCase):
    """Test that fetch scripts exit with non-zero code on 500 errors."""

    def setUp(self):
        self.logger = get_logger(__name__)
        # Create a temporary directory for any potential file outputs
        self.temp_dir = tempfile.mkdtemp()

    @responses.activate
    def test_500_exit_code_gdelt(self):
        """Mock 500 errors for GDELT and assert the script exits with code 1."""
        # Mock the GDELT API endpoint to return 500 errors
        # Assuming the fetch logic uses a GET request to a specific URL
        # We mock the specific URL pattern used by fetch_with_retry
        responses.add(
            responses.GET,
            responses.regexp(r'.*'),  # Catch-all for the specific API call
            status=500,
            body="Internal Server Error"
        )
        
        # We need to patch sys.exit to capture the exit code
        with patch('sys.exit') as mock_exit:
            with patch('sys.argv', ['fetch_gdelt.py']):
                # Also patch the specific output path to point to temp_dir if needed
                # or ensure the script doesn't crash before exit due to file IO
                try:
                    main_gdelt()
                except SystemExit:
                    pass # sys.exit raises SystemExit, we catch it in mock_exit
                
                # Verify sys.exit was called with a non-zero code
                mock_exit.assert_called()
                call_args = mock_exit.call_args[0][0]
                self.assertNotEqual(call_args, 0, "Script should exit with non-zero code on 500 error")

    @responses.activate
    def test_500_exit_code_trends(self):
        """Mock 500 errors for Google Trends and assert the script exits with code 1."""
        # Mock the Google Trends API endpoint to return 500 errors
        responses.add(
            responses.GET,
            responses.regexp(r'.*'),
            status=500,
            body="Internal Server Error"
        )
        
        with patch('sys.exit') as mock_exit:
            with patch('sys.argv', ['fetch_google_trends.py']):
                try:
                    main_trends()
                except SystemExit:
                    pass
                
                # Verify sys.exit was called with a non-zero code
                mock_exit.assert_called()
                call_args = mock_exit.call_args[0][0]
                self.assertNotEqual(call_args, 0, "Script should exit with non-zero code on 500 error")

    @responses.activate
    def test_retry_logic_on_failure(self):
        """Verify that the fetch logic retries on failure before exiting."""
        # This test verifies the retry behavior specifically for GDELT
        # We expect 3 failures (500) then the script exits
        # Note: The actual retry count depends on implementation in fetch_gdelt.py
        # Assuming standard 3 retries logic: 1 initial + 2 retries = 3 calls total before exit
        
        # We will track the number of calls to the mocked endpoint
        call_count = 0
        
        def request_callback(request):
            nonlocal call_count
            call_count += 1
            return (500, {}, "Internal Server Error")

        responses.add_callback(
            responses.GET,
            responses.regexp(r'.*'),
            callback=request_callback
        )

        with patch('sys.exit') as mock_exit:
            with patch('sys.argv', ['fetch_gdelt.py']):
                try:
                    main_gdelt()
                except SystemExit:
                    pass
            
            # Assert that the script attempted to fetch multiple times (retry logic)
            # and then exited. The exact count depends on the retry implementation in fetch_gdelt.py.
            # Typically: 1st attempt (fail), 2nd attempt (fail), 3rd attempt (fail) -> Exit.
            # So call_count should be at least 3 if retry logic is active.
            self.assertGreaterEqual(call_count, 2, "Script should retry at least once before exiting")
            mock_exit.assert_called()

if __name__ == '__main__':
    unittest.main()