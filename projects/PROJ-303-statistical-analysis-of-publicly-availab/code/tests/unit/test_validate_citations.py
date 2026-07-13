"""
Unit tests for src/scripts/validate_citations.py logic.

Since the script involves network I/O, these tests mock the network responses
to ensure the logic handles success and failure cases correctly without
requiring an actual internet connection during unit testing.
"""
import sys
import unittest
from unittest.mock import patch, MagicMock
import requests

# Add the src directory to the path to import the script logic
# We import the functions defined in the script, not the main entry point directly
# to avoid sys.exit() calls during tests.

# We will simulate the module content or import the functions if possible.
# Since validate_citations.py is a script, we'll define the functions here
# or import them if we refactor slightly. For now, we'll test the logic
# by importing the specific functions if the script structure allows,
# or by mocking the network calls in a test harness.

# To keep it simple and compliant with "extend, don't re-author", we assume
# the script can be imported. If it uses `if __name__ == "__main__":`,
# the functions are still available.

try:
    from src.scripts.validate_citations import check_url_availability, build_test_urls
except ImportError:
    # Fallback if path setup is different in test environment
    sys.path.insert(0, 'code')
    from src.scripts.validate_citations import check_url_availability, build_test_urls


class TestUrlValidation(unittest.TestCase):

    def test_build_test_urls_structure(self):
        """Verifies that the URL builder creates the expected number of URLs."""
        urls = build_test_urls()
        # 10 stations * 3 years = 30 URLs
        self.assertEqual(len(urls), 30)
        self.assertTrue(all(url.startswith("https://www.ncei.noaa.gov") for url in urls))
        self.assertTrue(all("ghcnd_" in url for url in urls))

    @patch('src.scripts.validate_citations.requests.head')
    def test_check_url_success(self, mock_head):
        """Tests the success path for URL availability check."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_head.return_value = mock_response

        is_ok, msg = check_url_availability("http://example.com/test")
        
        self.assertTrue(is_ok)
        self.assertEqual(msg, "OK")
        mock_head.assert_called_once()

    @patch('src.scripts.validate_citations.requests.head')
    def test_check_url_405_fallback(self, mock_head):
        """Tests the fallback to GET when HEAD returns 405."""
        # First call (HEAD) returns 405
        mock_head.return_value.status_code = 405
        
        # We need to mock GET as well
        with patch('src.scripts.validate_citations.requests.get') as mock_get:
            mock_get_response = MagicMock()
            mock_get_response.status_code = 200
            mock_get.return_value = mock_get_response

            is_ok, msg = check_url_availability("http://example.com/test")
            
            self.assertTrue(is_ok)
            self.assertIn("GET fallback", msg)
            mock_head.assert_called_once()
            mock_get.assert_called_once()

    @patch('src.scripts.validate_citations.requests.head')
    def test_check_url_timeout(self, mock_head):
        """Tests the timeout handling."""
        mock_head.side_effect = requests.exceptions.Timeout()

        is_ok, msg = check_url_availability("http://slow.com/test")
        
        self.assertFalse(is_ok)
        self.assertEqual(msg, "Timeout")

    @patch('src.scripts.validate_citations.requests.head')
    def test_check_url_connection_error(self, mock_head):
        """Tests the connection error handling."""
        mock_head.side_effect = requests.exceptions.ConnectionError()

        is_ok, msg = check_url_availability("http://nonexistent.com/test")
        
        self.assertFalse(is_ok)
        self.assertEqual(msg, "Connection Error")

    @patch('src.scripts.validate_citations.requests.head')
    def test_check_url_http_error(self, mock_head):
        """Tests handling of non-success HTTP status codes."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_head.return_value = mock_response

        is_ok, msg = check_url_availability("http://example.com/missing")
        
        self.assertFalse(is_ok)
        self.assertIn("404", msg)


if __name__ == '__main__':
    unittest.main()