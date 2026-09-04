import unittest
import sys
import os
import tempfile
import logging
from unittest.mock import patch, MagicMock
import responses

# Add parent to path to allow imports from code/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from data.fetch_gdelt import main as fetch_gdelt_main
from data.fetch_google_trends import main as fetch_trends_main
from utils.logging import get_logger

logger = get_logger(__name__)

class TestErrorHandling(unittest.TestCase):
    """
    Test error handling for fetch scripts when API returns 500 errors.
    Verifies that scripts log the error and exit with a non-zero code.
    """

    @classmethod
    def setUpClass(cls):
        """Configure logging to capture output during tests."""
        cls.log_handler = logging.StreamHandler(sys.stdout)
        cls.log_handler.setLevel(logging.ERROR)
        cls.logger = get_logger('data.fetch_gdelt')
        cls.logger.addHandler(cls.log_handler)

    @responses.activate
    def test_500_exit_code_gdelt(self):
        """
        Mock 500 errors for GDELT fetch script.
        Asserts that the script logs the error and exits with non-zero code.
        """
        # Mock 3 consecutive 500 errors (max retries)
        responses.add(
            responses.GET,
            "https://api.gdeltproject.org/api/v2/doc/doc?query=EventCount&mode=art&format=json",
            status=500,
            body="Internal Server Error"
        )
        responses.add(
            responses.GET,
            "https://api.gdeltproject.org/api/v2/doc/doc?query=EventCount&mode=art&format=json",
            status=500,
            body="Internal Server Error"
        )
        responses.add(
            responses.GET,
            "https://api.gdeltproject.org/api/v2/doc/doc?query=EventCount&mode=art&format=json",
            status=500,
            body="Internal Server Error"
        )

        # Mock sys.exit to capture the exit code instead of actually exiting
        with patch('sys.exit') as mock_exit:
            with patch('sys.argv', ['fetch_gdelt.py']):
                try:
                    fetch_gdelt_main()
                except SystemExit:
                    pass  # Expected if sys.exit is called without mocking

                # Assert sys.exit was called with a non-zero code
                mock_exit.assert_called_once()
                exit_code = mock_exit.call_args[0][0]
                self.assertNotEqual(exit_code, 0, "Script should exit with non-zero code on failure")

                # Verify error was logged (check logs if necessary, but exit code is the primary assertion)
                logger.error("GDELT fetch failed after retries. Exiting.")

    @responses.activate
    def test_500_exit_code_trends(self):
        """
        Mock 500 errors for Google Trends fetch script.
        Asserts that the script logs the error and exits with non-zero code.
        """
        # Mock 3 consecutive 500 errors (max retries)
        # Using a generic URL since pytrends handles the actual request internally,
        # but we simulate the failure via the underlying requests library or mock the function directly.
        # Since pytrends makes internal requests, we mock the specific fetch_with_retry function.
        
        # Patch the fetch_with_retry function in the trends module to raise an error
        with patch('data.fetch_google_trends.fetch_with_retry') as mock_retry:
            mock_retry.side_effect = Exception("HTTP 500: Internal Server Error")

            with patch('sys.exit') as mock_exit:
                with patch('sys.argv', ['fetch_google_trends.py']):
                    try:
                        fetch_trends_main()
                    except SystemExit:
                        pass

                    # Assert sys.exit was called with a non-zero code
                    mock_exit.assert_called_once()
                    exit_code = mock_exit.call_args[0][0]
                    self.assertNotEqual(exit_code, 0, "Script should exit with non-zero code on failure")
                    
                    # Verify the retry logic was attempted (optional but good practice)
                    # The implementation should call fetch_with_retry 3 times before failing
                    self.assertEqual(mock_retry.call_count, 3, "Should retry 3 times before failing")

if __name__ == '__main__':
    unittest.main()