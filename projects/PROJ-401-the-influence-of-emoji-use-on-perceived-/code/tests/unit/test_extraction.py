"""
Unit tests for emoji extraction logic in src/data/preprocessing.py.

Tests cover:
- Empty text
- Text with no emojis
- Text with single emoji
- Text with multiple emojis
- Text with skin tone modifiers
- Unicode normalization edge cases
"""
import pytest
from src.data.preprocessing import extract_emoji_features

class TestEmojiExtraction:
    def test_empty_text(self):
        """Test that empty text returns default values."""
        result = extract_emoji_features("")
        assert result["emoji_present"] is False
        assert result["emoji_count"] == 0
        assert result["emoji_types"] == []

    def test_none_text(self):
        """Test that None text is handled gracefully."""
        result = extract_emoji_features(None)
        assert result["emoji_present"] is False
        assert result["emoji_count"] == 0
        assert result["emoji_types"] == []

    def test_no_emoji(self):
        """Test text without emojis."""
        text = "Hello, world! This is a test."
        result = extract_emoji_features(text)
        assert result["emoji_present"] is False
        assert result["emoji_count"] == 0
        assert result["emoji_types"] == []

    def test_single_emoji(self):
        """Test text with a single emoji."""
        text = "Hello 👋"
        result = extract_emoji_features(text)
        assert result["emoji_present"] is True
        assert result["emoji_count"] == 1
        assert "👋" in result["emoji_types"]

    def test_multiple_emojis(self):
        """Test text with multiple emojis."""
        text = "I love 🍕 and 🍔!"
        result = extract_emoji_features(text)
        assert result["emoji_present"] is True
        assert result["emoji_count"] == 2
        assert "🍕" in result["emoji_types"]
        assert "🍔" in result["emoji_types"]
        assert len(result["emoji_types"]) == 2

    def test_duplicate_emojis(self):
        """Test that duplicate emojis are counted but unique types are distinct."""
        text = "👍 👍 👍"
        result = extract_emoji_features(text)
        assert result["emoji_present"] is True
        assert result["emoji_count"] == 3
        assert len(result["emoji_types"]) == 1
        assert "👍" in result["emoji_types"]

    def test_skin_tone_modifiers(self):
        """Test that skin tone modifiers are normalized to base emoji."""
        # 👍🏻 (Thumbs up + Light Skin Tone)
        # 👍🏿 (Thumbs up + Dark Skin Tone)
        # These should both normalize to "👍"
        text = "👍🏻 and 👍🏿"
        result = extract_emoji_features(text)
        assert result["emoji_present"] is True
        assert result["emoji_count"] == 2
        # Both should normalize to the base "👍"
        assert "👍" in result["emoji_types"]
        assert len(result["emoji_types"]) == 1

    def test_mixed_emojis_and_skin_tones(self):
        """Test mixed emojis with and without skin tones."""
        text = "👍🏻 👎 😊"
        result = extract_emoji_features(text)
        assert result["emoji_present"] is True
        assert result["emoji_count"] == 3
        # 👍🏻 -> 👍, 👎 -> 👎, 😊 -> 😊
        # Unique types: 👍, 👎, 😊
        assert "👍" in result["emoji_types"]
        assert "👎" in result["emoji_types"]
        assert "😊" in result["emoji_types"]
        assert len(result["emoji_types"]) == 3

    def test_complex_unicode(self):
        """Test text with complex Unicode sequences (e.g., flags)."""
        # Flags are often composed of two regional indicator symbols
        # e.g., 🇺🇸 (U + 🇸)
        text = "USA 🇺🇸"
        result = extract_emoji_features(text)
        # The library should recognize the flag as an emoji
        assert result["emoji_present"] is True
        assert result["emoji_count"] >= 1
        # The exact base type might be the flag sequence itself
        assert len(result["emoji_types"]) >= 1

    def test_emoji_in_middle_of_text(self):
        """Test emoji surrounded by text."""
        text = "Start middle 🚀 end"
        result = extract_emoji_features(text)
        assert result["emoji_present"] is True
        assert result["emoji_count"] == 1
        assert "🚀" in result["emoji_types"]

    def test_emoji_with_punctuation(self):
        """Test emoji with adjacent punctuation."""
        text = "Wow! 😲? Really?"
        result = extract_emoji_features(text)
        assert result["emoji_present"] is True
        assert result["emoji_count"] == 1
        assert "😲" in result["emoji_types"]