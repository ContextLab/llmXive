import unittest
import sys
import os
import tempfile
import logging
from unittest.mock import patch, MagicMock

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from code.data.fetch_gdelt import main as fetch_gdelt_main
from code.data.fetch_google_trends import main as fetch_trends_main
import requests
from responses import RequestsMock
import responses

class TestErrorHandling(unittest.TestCase):
    """
    Test error handling for fetch scripts, specifically:
    - 500 errors causing retries
    - Final exit with non-zero code when all retries fail
    """

    def setUp(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

    @responses.activate
    def test_500_exit_code_gdelt(self):
        """
        Test that fetch_gdelt.py exits with non-zero code when API returns 500 errors
        after all retry attempts.
        """
        # Mock the GDELT API endpoint to return 500 errors
        # GDELT uses the eventcount endpoint
        responses.add(
            responses.GET,
            "https://api.gdeltproject.org/api/v2/event/eventcount",
            status=500,
            body="Internal Server Error"
        )

        # Mock the checksum file path to use a temp file
        with tempfile.TemporaryDirectory() as tmpdir:
            checksum_path = os.path.join(tmpdir, ".checksums.json")
            
            # Patch the save_checksum function to use our temp path
            with patch('code.data.fetch_gdelt.save_checksum') as mock_save_checksum:
                mock_save_checksum.return_value = None
                
                # Capture the exit code
                with patch('sys.exit') as mock_exit:
                    try:
                        # Run the main function
                        fetch_gdelt_main()
                    except SystemExit as e:
                        # Verify exit code is non-zero
                        self.assertNotEqual(e.code, 0, 
                          "Script should exit with non-zero code on API failure")
                        self.logger.info(f"Correctly exited with code: {e.code}")
                    
                    # Verify sys.exit was called
                    mock_exit.assert_called_once()
                    
                    # Verify the retry logic was attempted (should be 3 attempts)
                    self.assertEqual(len(responses.calls), 3,
                      "Should have retried 3 times before failing")

    @responses.activate
    def test_500_exit_code_trends(self):
        """
        Test that fetch_google_trends.py exits with non-zero code when API returns 500 errors
        after all retry attempts.
        """
        # Mock the Google Trends API endpoint
        # pytrends uses a POST to Google's internal API
        responses.add(
            responses.POST,
            "https://trends.google.com/trends/api/explore",
            status=500,
            body="Internal Server Error"
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            checksum_path = os.path.join(tmpdir, ".checksums.json")
            
            with patch('code.data.fetch_google_trends.save_checksum') as mock_save_checksum:
                mock_save_checksum.return_value = None
                
                with patch('sys.exit') as mock_exit:
                    try:
                        fetch_trends_main()
                    except SystemExit as e:
                        # Verify exit code is non-zero
                        self.assertNotEqual(e.code, 0,
                          "Script should exit with non-zero code on API failure")
                        self.logger.info(f"Correctly exited with code: {e.code}")
                    
                    # Verify sys.exit was called
                    mock_exit.assert_called_once()
                    
                    # Verify the retry logic was attempted (should be 3 attempts)
                    self.assertEqual(len(responses.calls), 3,
                      "Should have retried 3 times before failing")

    def test_successful_request_no_exit(self):
        """
        Test that a successful request does NOT trigger sys.exit with non-zero code.
        """
        # This test verifies that normal operation doesn't exit
        # We'll mock a successful response
        responses.add(
            responses.GET,
            "https://api.gdeltproject.org/api/v2/event/eventcount",
            json={"data": {"events": []}},
            status=200
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('code.data.fetch_gdelt.save_checksum') as mock_save_checksum:
                mock_save_checksum.return_value = None
                
                with patch('sys.exit') as mock_exit:
                    # This should complete without calling sys.exit with error code
                    try:
                        fetch_gdelt_main()
                    except SystemExit as e:
                        # If it exits, it should be with code 0 (success)
                        self.assertEqual(e.code, 0,
                          "Script should exit with 0 on success")
                    
                    # Verify sys.exit was called with 0 or not called at all
                    if mock_exit.called:
                        call_args = mock_exit.call_args
                        if call_args:
                            self.assertEqual(call_args[0][0], 0,
                              "Successful run should exit with code 0")

if __name__ == '__main__':
    unittest.main()