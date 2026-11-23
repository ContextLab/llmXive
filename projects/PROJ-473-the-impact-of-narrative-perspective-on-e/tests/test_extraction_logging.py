import os
import tempfile
import logging
import unittest
from unittest.mock import patch
from io import StringIO

# Import the function to test
from extraction import extract_perspective_features

class TestExtractionLogging(unittest.TestCase):

    def setUp(self):
        # Set up a string buffer to capture log output
        self.log_stream = StringIO()
        self.handler = logging.StreamHandler(self.log_stream)
        self.handler.setLevel(logging.WARNING)
        self.logger = logging.getLogger('extraction')
        self.logger.addHandler(self.handler)
        self.logger.setLevel(logging.WARNING)

    def tearDown(self):
        self.logger.removeHandler(self.handler)

    def test_data_quality_insufficient_short_text(self):
        """Test that 'data_quality_insufficient' warning is logged for short texts."""
        # Create a temporary file with very short text (< 100 words)
        short_text = "This is a very short text. It has fewer than one hundred words. Just a few sentences here."
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(short_text)
            temp_path = f.name

        try:
            # Run extraction
            result = extract_perspective_features(temp_path)
            
            # Get log output
            log_contents = self.log_stream.getvalue()
            
            # Verify the warning was logged
            self.assertIn("data_quality_insufficient", log_contents)
            self.assertIn("insufficient for robust perspective analysis", log_contents)
            
            # Verify the flag is set in the result
            self.assertIsNotNone(result)
            self.assertTrue(result['quality_flags']['data_quality_insufficient'])
        finally:
            os.unlink(temp_path)

    def test_data_quality_insufficient_no_pronouns(self):
        """Test that 'data_quality_insufficient' warning is logged for texts with no pronouns."""
        # Create a text with no personal pronouns
        no_pronoun_text = """
        The mountain stood tall. The wind blew through the valley. Birds flew overhead.
        The river ran cold. Stones were scattered on the path. Silence filled the air.
        This continues for a long time to ensure word count is sufficient but pronouns are absent.
        """
        # Pad to ensure > 100 words but still no pronouns
        no_pronoun_text += " " + " ".join(["The scene remained static."] * 20)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(no_pronoun_text)
            temp_path = f.name

        try:
            result = extract_perspective_features(temp_path)
            
            log_contents = self.log_stream.getvalue()
            
            # Verify the warning was logged
            self.assertIn("data_quality_insufficient", log_contents)
            self.assertIn("no detected personal pronouns", log_contents)
            
            self.assertIsNotNone(result)
            self.assertTrue(result['quality_flags']['data_quality_insufficient'])
        finally:
            os.unlink(temp_path)

    def test_normal_text_no_warning(self):
        """Test that normal text does not trigger data_quality_insufficient warning."""
        normal_text = """
        I walked down the street. She was waiting for me. We talked about the weather.
        It was raining heavily. They said it would stop soon. I decided to stay inside.
        My friends joined me later. We played games. It was a good day.
        """
        # Pad to ensure > 100 words
        normal_text += " " + " ".join(["I thought about the day."] * 10)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(normal_text)
            temp_path = f.name

        try:
            result = extract_perspective_features(temp_path)
            
            log_contents = self.log_stream.getvalue()
            
            # Verify NO data_quality_insufficient warning
            self.assertNotIn("data_quality_insufficient", log_contents)
            
            self.assertIsNotNone(result)
            self.assertFalse(result['quality_flags']['data_quality_insufficient'])
        finally:
            os.unlink(temp_path)

if __name__ == '__main__':
    unittest.main()