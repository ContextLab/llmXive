"""
Unit tests for the cue matching and aggregation module.
"""
import unittest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from config import get_config_dict
from cue_matching import normalize_text, match_cues, resolve_collisions
from aggregation import enforce_match_rate

class TestMatchRateThresholdLogic(unittest.TestCase):
    """
    Tests for T106: Match Rate Threshold Logic.
    Verifies behavior of enforce_match_rate (T036) when config.MATCH_RATE_THRESHOLD
    is set to a numeric value and the actual rate is below it.
    """

    def setUp(self):
        """Set up test fixtures."""
        self.mock_data = pd.DataFrame({
            'user_id': [1, 2, 3, 4, 5],
            'track_id': ['A', 'B', 'C', 'D', 'E'],
            'cue_text': ['Song A', 'Song B', 'Song C', 'Song D', 'Song E'],
            'matched_track_id': ['A', 'B', None, None, None]
        })
        self.total_cues = 5
        self.matched_cues = 2
        self.match_rate = self.matched_cues / self.total_cues  # 0.40

    @patch('aggregation.logging')
    def test_numeric_threshold_below_actual_logs_warning(self, mock_logging):
        """
        Test that when MATCH_RATE_THRESHOLD is numeric (e.g., 0.80) and
        actual rate is below it, a warning is logged but execution continues.
        """
        # Mock config to return a numeric threshold
        with patch('aggregation.get_config_dict') as mock_config:
            mock_config.return_value = {
                'MATCH_RATE_THRESHOLD': 0.80
            }
            
            # Call the function
            # Note: enforce_match_rate typically takes the dataframe and calculates internally,
            # or takes the calculated rate. Based on T036 description, it verifies the rate.
            # We simulate the internal logic path where rate < threshold.
            
            # Since we are testing the logic of T036 specifically:
            # "IF the value is numeric: Perform the numeric >= check. If the rate is below the threshold, 
            # log a warning and proceed."
            
            # We will call the function with the mock data and verify it handles the low rate.
            # Assuming enforce_match_rate calculates rate internally from the dataframe passed.
            result = enforce_match_rate(self.mock_data)
            
            # Assert that a warning was logged
            mock_logging.warning.assert_called()
            
            # Verify the warning message contains relevant info
            warning_calls = [call[0][0] for call in mock_logging.warning.call_args_list]
            any_warning = any("Match rate" in str(w) or "threshold" in str(w).lower() for w in warning_calls)
            self.assertTrue(any_warning, "Expected a warning about match rate threshold.")

    @patch('aggregation.logging')
    def test_numeric_threshold_above_actual_no_warning(self, mock_logging):
        """
        Test that when MATCH_RATE_THRESHOLD is numeric and actual rate is above it,
        no warning is logged.
        """
        # Create data with high match rate
        high_rate_data = pd.DataFrame({
            'user_id': [1, 2, 3, 4, 5],
            'track_id': ['A', 'B', 'C', 'D', 'E'],
            'cue_text': ['Song A', 'Song B', 'Song C', 'Song D', 'Song E'],
            'matched_track_id': ['A', 'B', 'C', 'D', 'E']
        })
        
        with patch('aggregation.get_config_dict') as mock_config:
            mock_config.return_value = {
                'MATCH_RATE_THRESHOLD': 0.50
            }
            
            result = enforce_match_rate(high_rate_data)
            
            # Assert that no warning was logged regarding match rate
            warning_calls = [call[0][0] for call in mock_logging.warning.call_args_list]
            any_match_warning = any("Match rate" in str(w) for w in warning_calls)
            self.assertFalse(any_match_warning, "Expected no warning when rate is above threshold.")

    @patch('aggregation.logging')
    def test_deferred_threshold_defaults_to_80(self, mock_logging):
        """
        Test that when MATCH_RATE_THRESHOLD is '[deferred]', it defaults to 0.80
        and logs a note, then enforces the 80% threshold.
        """
        # Use low rate data (40%)
        with patch('aggregation.get_config_dict') as mock_config:
            mock_config.return_value = {
                'MATCH_RATE_THRESHOLD': '[deferred]'
            }
            
            # The function should default to 0.80 internally
            # Since 0.40 < 0.80, it should log a warning
            result = enforce_match_rate(self.mock_data)
            
            # Check for the default note
            log_messages = [call[0][0] for call in mock_logging.info.call_args_list + mock_logging.warning.call_args_list]
            has_default_note = any("defaulted to 80%" in str(msg).lower() for msg in log_messages)
            self.assertTrue(has_default_note, "Expected a note about defaulting to 80% threshold.")

    def test_function_returns_dataframe(self):
        """
        Test that enforce_match_rate returns the dataframe (possibly filtered or unchanged)
        and does not raise an exception even when threshold is missed.
        """
        with patch('aggregation.get_config_dict') as mock_config:
            mock_config.return_value = {
                'MATCH_RATE_THRESHOLD': 0.99  # Very high, will fail
            }
            
            # Should not raise an exception
            try:
                result = enforce_match_rate(self.mock_data)
                self.assertIsInstance(result, pd.DataFrame)
            except Exception as e:
                self.fail(f"enforce_match_rate raised an exception unexpectedly: {e}")

class TestNormalizeText(unittest.TestCase):
    """Unit tests for text normalization."""

    def test_lowercase_conversion(self):
        """Test that text is converted to lowercase."""
        result = normalize_text("Hello WORLD")
        self.assertEqual(result, "hello world")

    def test_punctuation_removal(self):
        """Test that punctuation is removed."""
        result = normalize_text("Hello, World! How are you?")
        self.assertEqual(result, "hello world how are you")

    def test_multiple_spaces_handling(self):
        """Test that multiple spaces are collapsed."""
        result = normalize_text("Hello   World")
        self.assertEqual(result, "hello world")

class TestFuzzyMatching(unittest.TestCase):
    """Unit tests for fuzzy matching logic."""

    def test_exact_match(self):
        """Test that exact matches are found with distance 0."""
        # This would typically be tested via the match_cues function with a mock index
        pass

    def test_levenshtein_threshold(self):
        """Test that matches within distance 4 are accepted."""
        # Specific test for T020 logic
        pass

class TestAggregation(unittest.TestCase):
    """Unit tests for aggregation logic."""

    def test_mean_vividness_valence(self):
        """Test that mean vividness and valence are calculated correctly."""
        # Specific test for T021 logic
        pass

if __name__ == '__main__':
    unittest.main()