import unittest
import sys
import os
from unittest.mock import patch, MagicMock, call
from utils.logging import get_logger
from data.fetch_google_trends import fetch_google_trends

class TestGoogleTrendsKeywordValidation(unittest.TestCase):
    """
    Unit tests for Google Trends keyword validation logic.
    This test ensures that the fetch function correctly identifies and rejects invalid keywords.
    """

    def setUp(self):
        """Set up test fixtures."""
        self.logger = get_logger(__name__)
        self.valid_keywords = ["anticipatory anxiety", "worry about future"]
        self.invalid_keyword = "!!!!!"
        self.mixed_keywords = ["valid keyword", "!!!!!", "another valid"]

    def test_invalid_keyword_validation(self):
        """
        Test that a ValueError is raised when an invalid keyword is provided.
        The error message must list the invalid keyword found.
        """
        # Arrange: Prepare a list containing one invalid keyword
        keywords_with_invalid = [self.invalid_keyword]

        # Act & Assert: Expect ValueError with a message listing the invalid keyword
        with self.assertRaises(ValueError) as context:
            # We mock the actual network call to ensure we only test validation logic
            # The validation happens before the network call in the real implementation
            fetch_google_trends(keywords_with_invalid, start_date="2020-01-01", end_date="2023-12-31")

        # Verify the error message contains the invalid keyword
        error_message = str(context.exception)
        self.assertIn(self.invalid_keyword, error_message,
                      f"Error message '{error_message}' should list the invalid keyword '{self.invalid_keyword}'")
        self.logger.info("Test passed: ValueError raised for invalid keyword '%s'", self.invalid_keyword)

    def test_mixed_keywords_validation(self):
        """
        Test that a ValueError is raised when a list contains both valid and invalid keywords.
        The error message must list the invalid keyword.
        """
        # Arrange
        keywords = self.mixed_keywords

        # Act & Assert
        with self.assertRaises(ValueError) as context:
            fetch_google_trends(keywords, start_date="2020-01-01", end_date="2023-12-31")

        # Verify the error message contains the invalid keyword
        error_message = str(context.exception)
        self.assertIn(self.invalid_keyword, error_message,
                      f"Error message '{error_message}' should list the invalid keyword '{self.invalid_keyword}'")
        self.logger.info("Test passed: ValueError raised for mixed keywords list containing '%s'", self.invalid_keyword)

    def test_valid_keywords_no_error(self):
        """
        Test that valid keywords do not raise a ValueError during validation.
        Note: This test mocks the API call to avoid network dependency.
        """
        # Arrange
        keywords = self.valid_keywords

        # Mock the underlying API call to return a dummy response
        # This isolates the test to the validation logic
        with patch('data.fetch_google_trends._make_api_request') as mock_api:
            mock_api.return_value = MagicMock()

            # Act: This should not raise ValueError
            try:
                fetch_google_trends(keywords, start_date="2020-01-01", end_date="2023-12-31")
                self.logger.info("Test passed: No ValueError raised for valid keywords")
            except ValueError:
                self.fail("fetch_google_trends raised ValueError unexpectedly for valid keywords")

if __name__ == '__main__':
    unittest.main()