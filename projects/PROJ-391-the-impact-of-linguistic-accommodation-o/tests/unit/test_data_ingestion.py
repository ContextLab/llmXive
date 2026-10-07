"""
Unit tests for empty record filtering in code/data/ingestion.py.

This module verifies that the `preprocess_dialogue_pair` function correctly
identifies and filters out records where the turn or partner turn is empty
or non-text after NFKC normalization.

Dependencies:
- code/utils.py (normalize_text, is_valid_text)
- code/data/ingestion.py (preprocess_dialogue_pair)
"""
import pytest
import pandas as pd
from pathlib import Path
import sys

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils import normalize_text, is_valid_text
from data.ingestion import preprocess_dialogue_pair


class TestEmptyRecordFiltering:
    """Tests for filtering empty or invalid text records."""

    def test_valid_text_passes_filter(self):
        """Test that valid, non-empty text records are kept."""
        turn = "Hello, how are you?"
        partner_turn = "I am doing well, thank you."
        
        result = preprocess_dialogue_pair(turn, partner_turn)
        
        assert result is not None, "Valid text should not be filtered out"
        assert result['turn'] == turn
        assert result['partner_turn'] == partner_turn
        assert result['is_valid'] is True

    def test_empty_string_turn_is_filtered(self):
        """Test that empty string turns are filtered out."""
        turn = ""
        partner_turn = "Hello there!"
        
        result = preprocess_dialogue_pair(turn, partner_turn)
        
        assert result is None, "Empty turn should be filtered out"

    def test_empty_string_partner_turn_is_filtered(self):
        """Test that empty string partner turns are filtered out."""
        turn = "Hello!"
        partner_turn = ""
        
        result = preprocess_dialogue_pair(turn, partner_turn)
        
        assert result is None, "Empty partner_turn should be filtered out"

    def test_whitespace_only_turn_is_filtered(self):
        """Test that whitespace-only turns are filtered out."""
        turn = "   \n\t  "
        partner_turn = "Hello!"
        
        result = preprocess_dialogue_pair(turn, partner_turn)
        
        assert result is None, "Whitespace-only turn should be filtered out"

    def test_whitespace_only_partner_turn_is_filtered(self):
        """Test that whitespace-only partner turns are filtered out."""
        turn = "Hello!"
        partner_turn = "   \n\t  "
        
        result = preprocess_dialogue_pair(turn, partner_turn)
        
        assert result is None, "Whitespace-only partner_turn should be filtered out"

    def test_none_turn_is_filtered(self):
        """Test that None turns are filtered out."""
        turn = None
        partner_turn = "Hello!"
        
        result = preprocess_dialogue_pair(turn, partner_turn)
        
        assert result is None, "None turn should be filtered out"

    def test_none_partner_turn_is_filtered(self):
        """Test that None partner turns are filtered out."""
        turn = "Hello!"
        partner_turn = None
        
        result = preprocess_dialogue_pair(turn, partner_turn)
        
        assert result is None, "None partner_turn should be filtered out"

    def test_normalization_handles_special_chars_but_keeps_valid(self):
        """Test that NFKC normalization processes text but keeps valid content."""
        # Unicode characters that should normalize to valid text
        turn = "Hëllö"  # Should normalize to "Hëllö" or similar valid text
        partner_turn = "Wörld"
        
        result = preprocess_dialogue_pair(turn, partner_turn)
        
        assert result is not None, "Text with special chars should not be filtered"
        assert result['is_valid'] is True

    def test_emoji_only_turn_is_filtered(self):
        """Test that turns containing only emojis (no text) are filtered if is_valid_text returns False."""
        # Note: is_valid_text checks if there's at least one alphanumeric character
        # Emojis alone might be considered invalid depending on the implementation
        turn = "😀😃😄"
        partner_turn = "Hello!"
        
        result = preprocess_dialogue_pair(turn, partner_turn)
        
        # Depending on is_valid_text implementation, this might be filtered
        # The test ensures the logic is consistent
        if not is_valid_text(turn):
            assert result is None, "Emoji-only turn should be filtered if is_valid_text returns False"
        else:
            assert result is not None, "Emoji-only turn should be kept if is_valid_text returns True"

    def test_text_with_emoji_passes(self):
        """Test that text containing both words and emojis is kept."""
        turn = "Hello! 😀 How are you?"
        partner_turn = "I'm great! 😊"
        
        result = preprocess_dialogue_pair(turn, partner_turn)
        
        assert result is not None, "Text with emojis should not be filtered"
        assert result['is_valid'] is True

    def test_mixed_valid_and_invalid_dataframe_filtering(self):
        """Test filtering a DataFrame with mixed valid and invalid records."""
        # Create a test DataFrame
        data = {
            'turn': [
                "Valid text",
                "",
                "   ",
                None,
                "Another valid",
                "\t\n"
            ],
            'partner_turn': [
                "Valid response",
                "Valid response",
                "Valid response",
                "Valid response",
                "",
                "Valid response"
            ],
            'conversation_id': [1, 2, 3, 4, 5, 6]
        }
        df = pd.DataFrame(data)
        
        # Apply filtering logic
        valid_records = []
        for _, row in df.iterrows():
            result = preprocess_dialogue_pair(row['turn'], row['partner_turn'])
            if result is not None:
                valid_records.append(result)
        
        # We expect 3 valid records (indices 0, 4, 5 - wait, index 4 has empty partner_turn)
        # Actually: 0 (valid), 1 (empty turn), 2 (whitespace turn), 3 (None turn), 4 (empty partner), 5 (whitespace turn)
        # Expected valid: only index 0
        assert len(valid_records) == 1, f"Expected 1 valid record, got {len(valid_records)}"
        assert valid_records[0]['conversation_id'] == 1

    def test_preprocess_returns_dict_with_required_keys(self):
        """Test that preprocess_dialogue_pair returns a dict with required keys."""
        turn = "Test"
        partner_turn = "Response"
        
        result = preprocess_dialogue_pair(turn, partner_turn)
        
        assert isinstance(result, dict), "Result should be a dictionary"
        assert 'turn' in result, "Result should contain 'turn' key"
        assert 'partner_turn' in result, "Result should contain 'partner_turn' key"
        assert 'is_valid' in result, "Result should contain 'is_valid' key"
        assert result['is_valid'] is True