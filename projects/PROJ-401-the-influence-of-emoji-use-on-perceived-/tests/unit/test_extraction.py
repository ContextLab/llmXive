"""
Unit tests for emoji extraction logic in src/data/preprocessing.py.

Tests cover:
- Empty text strings
- Text with skin tone modifiers
- Unicode normalization
"""
import pytest
from src.data.preprocessing import extract_emoji_features

def test_extract_emoji_empty_text():
    """Test extraction on empty string."""
    result = extract_emoji_features("")
    assert result["emoji_present"] is False
    assert result["emoji_count"] == 0
    assert result["emoji_types"] == []

def test_extract_emoji_no_emoji():
    """Test extraction on text without emojis."""
    text = "Hello world, this is a test."
    result = extract_emoji_features(text)
    assert result["emoji_present"] is False
    assert result["emoji_count"] == 0
    assert result["emoji_types"] == []

def test_extract_emoji_simple():
    """Test extraction with a simple emoji."""
    text = "I love coding! 😊"
    result = extract_emoji_features(text)
    assert result["emoji_present"] is True
    assert result["emoji_count"] == 1
    assert "smiling face" in result["emoji_types"][0].lower()

def test_extract_emoji_skin_tone_modifier():
    """Test extraction with skin tone modifiers (e.g., 👍🏻)."""
    text = "Thumbs up! 👍🏻"
    result = extract_emoji_features(text)
    assert result["emoji_present"] is True
    assert result["emoji_count"] >= 1
    # Verify the function handles the modifier correctly (should not crash)
    assert isinstance(result["emoji_types"], list)

def test_extract_emoji_multiple():
    """Test extraction with multiple emojis."""
    text = "Party time! 🎉🎊🥳"
    result = extract_emoji_features(text)
    assert result["emoji_present"] is True
    assert result["emoji_count"] == 3
    assert len(result["emoji_types"]) == 3

def test_extract_emoji_unicode_normalization():
    """Test that different Unicode representations are handled."""
    # Test with a flag emoji which is a sequence of regional indicators
    text = "Go USA! 🇺🇸"
    result = extract_emoji_features(text)
    assert result["emoji_present"] is True
    assert result["emoji_count"] >= 1
