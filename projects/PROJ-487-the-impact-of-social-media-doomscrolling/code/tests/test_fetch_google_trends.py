import unittest
import sys
import os
from unittest.mock import patch, MagicMock, call
from utils.logging import get_logger
from data.fetch_google_trends import fetch_google_trends

class TestGoogleTrendsKeywordValidation(unittest.TestCase):
    """
    Tests for Google Trends keyword validation logic.
    Specifically tests that invalid keywords raise a ValueError
    with a message listing the invalid keyword(s).
    """

    def setUp(self):
        self.logger = get_logger(__name__)

    @patch('data.fetch_google_trends.pytrends')
    def test_invalid_keyword_validation(self, mock_pytrends):
        """
        Verify that fetch_google_trends raises a ValueError when
        provided with a list containing an invalid keyword.
        The error message must list the invalid keyword.
        """
        # Arrange: Setup mock to avoid actual API calls, but we expect
        # the validation to happen before any API interaction.
        mock_trends = MagicMock()
        mock_pytrends.request.TrendReq.return_value = mock_trends

        # Define an invalid keyword (e.g., containing only special characters)
        invalid_keywords = ["!!!!!", "valid_keyword"]

        # Act & Assert: The function should raise a ValueError
        # because "!!!!!" is not a valid search term for Google Trends.
        with self.assertRaises(ValueError) as context:
            fetch_google_trends(invalid_keywords, start_date="2023-01-01", end_date="2023-01-31")

        # Verify the error message contains the invalid keyword
        error_message = str(context.exception)
        self.assertIn("!!!!!", error_message,
                      f"Error message '{error_message}' should list the invalid keyword '!!!!!'")

        self.logger.info("Test passed: ValueError raised with correct message for invalid keyword.")

    @patch('data.fetch_google_trends.pytrends')
    def test_all_valid_keywords(self, mock_pytrends):
        """
        Verify that fetch_google_trends proceeds without raising an error
        when all keywords are valid (simulated by not raising in validation).
        """
        # Arrange
        mock_trends = MagicMock()
        mock_pytrends.request.TrendReq.return_value = mock_trends
        
        # Mock the build_payload and get_data methods to simulate success
        mock_trends.build_payload.return_value = mock_trends
        mock_trends.get_data.return_value = {"date": ["2023-01-01"], "value": [10]}

        valid_keywords = ["anticipatory anxiety", "worry about future"]

        # Act: This should not raise
        try:
            result = fetch_google_trends(valid_keywords, start_date="2023-01-01", end_date="2023-01-31")
            self.assertIsNotNone(result)
            self.logger.info("Test passed: Valid keywords processed successfully.")
        except ValueError:
            self.fail("fetch_google_trends raised ValueError for valid keywords unexpectedly.")

    def test_empty_keyword_list(self):
        """
        Verify that an empty list of keywords raises a ValueError.
        """
        # Act & Assert
        with self.assertRaises(ValueError) as context:
            fetch_google_trends([], start_date="2023-01-01", end_date="2023-01-31")
        
        self.assertIn("empty", str(context.exception).lower(),
                      "Error message should indicate the keyword list is empty.")

    @patch('data.fetch_google_trends.pytrends')
    def test_mixed_valid_invalid_keywords(self, mock_pytrends):
        """
        Verify that if a mix of valid and invalid keywords is provided,
        the invalid ones are caught and reported.
        """
        mock_trends = MagicMock()
        mock_pytrends.request.TrendReq.return_value = mock_trends

        mixed_keywords = ["valid_term", "123!@#", "another_valid"]

        with self.assertRaises(ValueError) as context:
            fetch_google_trends(mixed_keywords, start_date="2023-01-01", end_date="2023-01-31")

        error_message = str(context.exception)
        self.assertIn("123!@#", error_message,
                      f"Error message '{error_message}' should list the invalid keyword '123!@#'")
