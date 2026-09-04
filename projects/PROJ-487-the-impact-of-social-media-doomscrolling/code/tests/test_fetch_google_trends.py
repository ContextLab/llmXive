import unittest
import sys
import os
from unittest.mock import patch, MagicMock, call
from utils.logging import get_logger

# Ensure the project root is in the path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from data.fetch_google_trends import fetch_google_trends


class TestGoogleTrendsKeywordValidation(unittest.TestCase):
    """
    Unit tests for Google Trends keyword validation logic.
    Specifically tests that invalid keywords raise ValueError.
    """

    def setUp(self):
        self.logger = get_logger(__name__)

    @patch('data.fetch_google_trends.pytrends')
    @patch('data.fetch_google_trends.time')
    def test_invalid_keyword_validation(self, mock_time, mock_pytrends):
        """
        Test that passing a list containing an invalid keyword (e.g., "!!!!!")
        raises a ValueError with a message listing the invalid keyword.
        """
        # Setup mock
        mock_trend = MagicMock()
        mock_pytrends.TrendRequest.return_value = mock_trend

        # Valid keywords mixed with an invalid one
        invalid_keywords = ["anticipatory anxiety", "!!!!!"]
        start_date = "2023-01-01"
        end_date = "2023-01-31"
        geo = "US"

        # Expect ValueError to be raised
        with self.assertRaises(ValueError) as context:
            fetch_google_trends(invalid_keywords, start_date, end_date, geo)

        # Verify the error message contains the invalid keyword
        self.assertIn("!!!!!", str(context.exception))
        self.assertIn("invalid keyword", str(context.exception).lower())

    @patch('data.fetch_google_trends.pytrends')
    @patch('data.fetch_google_trends.time')
    def test_all_valid_keywords_pass(self, mock_time, mock_pytrends):
        """
        Test that a list of valid keywords does not raise an error.
        """
        # Setup mock
        mock_trend = MagicMock()
        mock_pytrends.TrendRequest.return_value = mock_trend

        # Simulate successful build
        mock_trend.build_payload.return_value = mock_trend
        mock_trend.interest_over_time.return_value = MagicMock()

        valid_keywords = ["anticipatory anxiety", "worry about future"]
        start_date = "2023-01-01"
        end_date = "2023-01-31"
        geo = "US"

        # Should not raise
        try:
            result = fetch_google_trends(valid_keywords, start_date, end_date, geo)
        except ValueError:
            self.fail("fetch_google_trends raised ValueError unexpectedly for valid keywords")

    @patch('data.fetch_google_trends.pytrends')
    @patch('data.fetch_google_trends.time')
    def test_empty_keyword_list_validation(self, mock_time, mock_pytrends):
        """
        Test that an empty list of keywords raises a ValueError.
        """
        # Setup mock
        mock_trend = MagicMock()
        mock_pytrends.TrendRequest.return_value = mock_trend

        empty_keywords = []
        start_date = "2023-01-01"
        end_date = "2023-01-31"
        geo = "US"

        # Expect ValueError
        with self.assertRaises(ValueError) as context:
            fetch_google_trends(empty_keywords, start_date, end_date, geo)

        self.assertIn("empty", str(context.exception).lower())


if __name__ == '__main__':
    unittest.main()