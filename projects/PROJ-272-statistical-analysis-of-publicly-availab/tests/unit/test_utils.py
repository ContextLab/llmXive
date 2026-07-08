"""
Unit tests for data validation utilities in code/utils.py.
"""
import pytest
from utils import normalize_text, validate_text_length


class TestNormalizeText:
    def test_string_passthrough(self):
        """Test that valid UTF-8 strings pass through correctly."""
        text = "Hello, world!"
        assert normalize_text(text) == "Hello, world!"

    def test_bytes_decoding(self):
        """Test that bytes are decoded to UTF-8."""
        text_bytes = b"Hello, world!"
        assert normalize_text(text_bytes) == "Hello, world!"

    def test_bytes_invalid_utf8_replacement(self):
        """Test that invalid UTF-8 bytes are replaced with replacement character."""
        # 0xFF is invalid in UTF-8
        text_bytes = b"\xff"
        result = normalize_text(text_bytes)
        assert "\ufffd" in result  # Replacement character

    def test_non_string_conversion(self):
        """Test that non-string types are converted to string."""
        assert normalize_text(123) == "123"
        assert normalize_text(3.14) == "3.14"

    def test_unicode_normalization(self):
        """Test that unicode is normalized to NFKC."""
        # 'é' can be composed (U+00E9) or decomposed (U+0065 + U+0301)
        composed = "\u00e9"
        decomposed = "e\u0301"
        
        result_composed = normalize_text(composed)
        result_decomposed = normalize_text(decomposed)
        
        # Both should normalize to the same string
        assert result_composed == result_decomposed == "é"


class TestValidateTextLength:
    def test_valid_word_count(self):
        """Test validation with valid word count."""
        text = "This is a short sentence."
        assert validate_text_length(text, min_length=3) is True

    def test_invalid_short_text(self):
        """Test validation rejects text below minimum."""
        text = "Hi"
        assert validate_text_length(text, min_length=5) is False

    def test_invalid_long_text(self):
        """Test validation rejects text above maximum."""
        text = "Word " * 100
        assert validate_text_length(text, max_length=50) is False

    def test_empty_string(self):
        """Test validation rejects empty string."""
        assert validate_text_length("", min_length=1) is False

    def test_char_count_mode(self):
        """Test validation using character count."""
        text = "Hello"
        assert validate_text_length(text, min_length=3, unit="chars") is True
        assert validate_text_length(text, max_length=3, unit="chars") is False

    def test_word_count_default(self):
        """Test that word count is the default unit."""
        text = "One two three"
        # 3 words
        assert validate_text_length(text, min_length=3) is True
        assert validate_text_length(text, min_length=4) is False