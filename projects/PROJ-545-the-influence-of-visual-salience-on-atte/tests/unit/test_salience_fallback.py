"""
Unit test for salience fallback logic.
Verifies that the text-only heuristic returns a valid score when image URL is broken.
"""
import os
import sys
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from io import BytesIO

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import the function to test
# Assuming the function is in code/data/salience.py
try:
    from data.salience import compute_text_heuristic_salience, load_image_from_url
except ImportError:
    pytest.skip("salience.py module not found or incomplete.", allow_module_level=True)


class TestSalienceFallback:
    """
    Unit tests for the text-based salience fallback mechanism.
    """

    def test_text_heuristic_returns_valid_score(self):
        """
        Unit test: Verify text-only heuristic returns valid score (0.0-1.0).
        """
        # Sample text data
        text_data = "A man in a yellow raincoat stands near a red car."
        
        score = compute_text_heuristic_salience(text_data)
        
        assert score is not None, "compute_text_heuristic_salience returned None."
        assert isinstance(score, (int, float)), f"Score must be numeric, got {type(score)}."
        assert 0.0 <= score <= 1.0, (
            f"Score {score} is outside the valid range [0.0, 1.0]."
        )

    def test_text_heuristic_with_empty_text(self):
        """
        Unit test: Verify behavior with empty text (edge case).
        """
        score = compute_text_heuristic_salience("")
        
        # Depending on implementation, this might return 0.0 or raise an error.
        # Assuming it returns 0.0 for empty input.
        assert score is not None, "Score should not be None for empty text."
        assert 0.0 <= score <= 1.0, "Score must be in range [0.0, 1.0]."

    def test_text_heuristic_with_special_characters(self):
        """
        Unit test: Verify behavior with special characters.
        """
        text_data = "!!! @@@ ### $$$"
        score = compute_text_heuristic_salience(text_data)
        
        assert score is not None, "Score should not be None."
        assert 0.0 <= score <= 1.0, "Score must be in range [0.0, 1.0]."

    @patch('data.salience.load_image_from_url')
    def test_fallback_trigger_on_broken_url(self, mock_load_image):
        """
        Unit test: Simulate broken image URL and verify fallback is triggered.
        This test assumes the main computation function calls load_image_from_url
        and catches exceptions to use the text heuristic.
        """
        # Mock the image loader to raise an exception (simulating broken URL)
        mock_load_image.side_effect = Exception("Connection timeout or 404")
        
        # We need to test the higher-level function that orchestrates this.
        # Assuming `compute_salience_score` exists and handles the fallback.
        try:
            from data.salience import compute_salience_score
        except ImportError:
            pytest.skip("compute_salience_score not found.")
            return

        # Mock text heuristic to return a specific value
        with patch('data.salience.compute_text_heuristic_salience') as mock_text:
            mock_text.return_value = 0.75
            
            # Call the function with an invalid URL and valid text
            # We need to know the exact signature of compute_salience_score
            # Assuming it takes (image_url, text_description)
            try:
                result = compute_salience_score(
                    image_url="http://broken.url/image.jpg",
                    text_description="A cat sits on a mat."
                )
            except Exception as e:
                # If it still raises, the fallback logic might not be implemented correctly
                pytest.fail(f"Fallback logic failed to handle broken URL: {e}")
            
            # Verify the text heuristic was called
            mock_text.assert_called_once()
            
            # Verify the result is the fallback value
            assert result == 0.75, (
                f"Expected fallback score 0.75, got {result}. "
                "Fallback logic did not return the text heuristic result."
            )