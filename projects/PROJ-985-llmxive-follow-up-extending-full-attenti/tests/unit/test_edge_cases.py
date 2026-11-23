"""
Unit tests for edge cases in data processing and feature extraction.
Covers special characters, emojis, empty inputs, and boundary conditions.
"""
import pytest
import sys
from pathlib import Path

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.compute_features import (
    is_ambiguous_token,
    get_token_category,
    compute_entropy,
    compute_kenlm_perplexity,
    compute_local_semantic_density,
)


class TestSpecialCharacters:
    """Test handling of special characters and symbols."""

    def test_is_ambiguous_token_special_chars(self):
        """Special characters should be flagged as ambiguous."""
        assert is_ambiguous_token("@") is True
        assert is_ambiguous_token("#") is True
        assert is_ambiguous_token("$") is True
        assert is_ambiguous_token("%") is True
        assert is_ambiguous_token("&") is True
        assert is_ambiguous_token("*") is True
        assert is_ambiguous_token("(") is True
        assert is_ambiguous_token(")") is True
        assert is_ambiguous_token("[") is True
        assert is_ambiguous_token("]") is True

    def test_is_ambiguous_token_emojis(self):
        """Emojis should be flagged as ambiguous."""
        assert is_ambiguous_token("😀") is True
        assert is_ambiguous_token("🚀") is True
        assert is_ambiguous_token("🌟") is True
        assert is_ambiguous_token("🔥") is True
        assert is_ambiguous_token("💯") is True

    def test_is_ambiguous_token_normal_text(self):
        """Normal alphanumeric tokens should not be ambiguous."""
        assert is_ambiguous_token("hello") is False
        assert is_ambiguous_token("world123") is False
        assert is_ambiguous_token("test") is False

    def test_get_token_category_special_chars(self):
        """Special characters should get neutral category."""
        assert get_token_category("@") == "neutral"
        assert get_token_category("#") == "neutral"
        assert get_token_category("$") == "neutral"

    def test_get_token_category_emojis(self):
        """Emojis should get neutral category."""
        assert get_token_category("😀") == "neutral"
        assert get_token_category("🚀") == "neutral"

    def test_get_token_category_normal_tokens(self):
        """Normal tokens should get appropriate categories."""
        assert get_token_category("hello") in ["noun", "verb", "adj", "adv", "other"]
        assert get_token_category("run") in ["noun", "verb", "adj", "adv", "other"]


class TestEmptyInputs:
    """Test handling of empty inputs."""

    def test_compute_entropy_empty_string(self):
        """Empty string should return 0.0 entropy."""
        assert compute_entropy("") == 0.0

    def test_compute_entropy_single_char(self):
        """Single character should have low entropy."""
        entropy = compute_entropy("a")
        assert entropy == 0.0  # Single char has no variation

    def test_compute_kenlm_perplexity_empty(self):
        """Empty string should return 1.0 perplexity (neutral)."""
        perplexity = compute_kenlm_perplexity("")
        assert perplexity == 1.0

    def test_compute_local_semantic_density_empty(self):
        """Empty token list should return 0.0 density."""
        density = compute_local_semantic_density([], 10)
        assert density == 0.0


class TestBoundaryConditions:
    """Test boundary conditions in sliding window operations."""

    def test_compute_local_semantic_density_start_boundary(self):
        """Test semantic density at the start of a document."""
        tokens = ["hello", "world", "test", "data", "example"]
        # Window size larger than available tokens at start
        density = compute_local_semantic_density(tokens, window_size=10)
        # Should handle boundary gracefully
        assert density >= 0.0
        assert density <= 1.0

    def test_compute_local_semantic_density_end_boundary(self):
        """Test semantic density at the end of a document."""
        tokens = ["hello", "world", "test", "data", "example"]
        # Access last token
        density = compute_local_semantic_density(tokens, window_size=10)
        assert density >= 0.0
        assert density <= 1.0

    def test_compute_entropy_uniform_distribution(self):
        """Test entropy with uniform character distribution."""
        text = "abcd"  # Each char appears once
        entropy = compute_entropy(text)
        assert entropy > 0.0

    def test_compute_entropy_repeated_chars(self):
        """Test entropy with repeated characters."""
        text = "aaaa"  # All same char
        entropy = compute_entropy(text)
        assert entropy == 0.0  # No variation


class TestUnicodeAndMultilingual:
    """Test handling of Unicode and multilingual text."""

    def test_is_ambiguous_token_unicode(self):
        """Unicode characters should be handled without crashing."""
        assert is_ambiguous_token("你好") is False  # Chinese
        assert is_ambiguous_token("مرحبا") is False  # Arabic
        assert is_ambiguous_token("Привет") is False  # Russian

    def test_compute_entropy_unicode(self):
        """Entropy calculation should work with Unicode."""
        text = "你好世界"
        entropy = compute_entropy(text)
        assert entropy >= 0.0

    def test_get_token_category_unicode(self):
        """Token category should handle Unicode gracefully."""
        category = get_token_category("你好")
        assert category in ["noun", "verb", "adj", "adv", "other", "neutral"]


class TestExtremeValues:
    """Test handling of extreme values and edge cases."""

    def test_compute_entropy_very_long_string(self):
        """Entropy should handle very long strings."""
        text = "a" * 10000
        entropy = compute_entropy(text)
        assert entropy == 0.0  # All same char

    def test_compute_entropy_highly_varied_string(self):
        """Entropy should be high for varied strings."""
        text = "abcdefghijklmnopqrstuvwxyz"
        entropy = compute_entropy(text)
        assert entropy > 1.0  # High variation

    def test_compute_local_semantic_density_single_token(self):
        """Semantic density with single token."""
        tokens = ["hello"]
        density = compute_local_semantic_density(tokens, window_size=10)
        assert density >= 0.0
        assert density <= 1.0

    def test_compute_local_semantic_density_all_unique(self):
        """Semantic density when all tokens are unique."""
        tokens = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j"]
        density = compute_local_semantic_density(tokens, window_size=10)
        # All unique should give high density
        assert density > 0.5

    def test_compute_local_semantic_density_all_same(self):
        """Semantic density when all tokens are the same."""
        tokens = ["a", "a", "a", "a", "a", "a", "a", "a", "a", "a"]
        density = compute_local_semantic_density(tokens, window_size=10)
        # All same should give low density
        assert density < 0.5