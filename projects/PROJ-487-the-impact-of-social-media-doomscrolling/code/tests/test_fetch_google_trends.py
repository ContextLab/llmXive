import unittest
import sys
import os

# Add the parent directory to the path to allow imports from code/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.fetch_google_trends import validate_keywords


class TestGoogleTrendsKeywordValidation(unittest.TestCase):
    """Unit tests for Google Trends keyword validation logic."""

    def test_invalid_keyword_validation(self):
        """
        Test that an invalid keyword (containing only special characters)
        raises a ValueError with a message listing the invalid keyword.
        """
        # Setup: A list containing one invalid keyword
        invalid_keywords = ["!!!!!", "ValidKeyword", "AnotherValid"]

        # Action & Assertion: Expect ValueError with specific message
        with self.assertRaises(ValueError) as context:
            validate_keywords(invalid_keywords)

        # Verify the error message contains the invalid keyword
        error_message = str(context.exception)
        self.assertIn("!!!!!", error_message)
        self.assertIn("Invalid keyword", error_message)

    def test_all_valid_keywords(self):
        """
        Test that a list of valid keywords passes validation without error.
        """
        # Setup: A list of valid keywords
        valid_keywords = ["anticipatory anxiety", "worry about future", "stress"]

        # Action: Should not raise
        try:
            validate_keywords(valid_keywords)
        except ValueError:
            self.fail("validate_keywords() raised ValueError unexpectedly for valid keywords")

    def test_empty_keyword_string(self):
        """
        Test that an empty string keyword raises a ValueError.
        """
        # Setup: A list containing an empty string
        invalid_keywords = ["", "valid"]

        # Action & Assertion: Expect ValueError
        with self.assertRaises(ValueError) as context:
            validate_keywords(invalid_keywords)

        # Verify the error message indicates the empty string
        error_message = str(context.exception)
        self.assertIn("empty", error_message.lower())

    def test_keyword_with_only_whitespace(self):
        """
        Test that a keyword consisting only of whitespace raises a ValueError.
        """
        # Setup: A list containing a whitespace-only string
        invalid_keywords = ["   ", "valid"]

        # Action & Assertion: Expect ValueError
        with self.assertRaises(ValueError) as context:
            validate_keywords(invalid_keywords)

        # Verify the error message indicates the issue
        error_message = str(context.exception)
        self.assertIn("whitespace", error_message.lower()) or self.assertIn("empty", error_message.lower())

    def test_multiple_invalid_keywords(self):
        """
        Test that if multiple invalid keywords exist, the error message lists them.
        """
        # Setup: A list with multiple invalid keywords
        invalid_keywords = ["!!!", "@@@@", "valid"]

        # Action & Assertion: Expect ValueError
        with self.assertRaises(ValueError) as context:
            validate_keywords(invalid_keywords)

        error_message = str(context.exception)
        self.assertIn("!!!", error_message)
        self.assertIn("@@@@", error_message)


if __name__ == '__main__':
    unittest.main()