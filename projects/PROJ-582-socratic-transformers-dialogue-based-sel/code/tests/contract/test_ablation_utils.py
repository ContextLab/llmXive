"""
Contract tests for ablation_utils (T015a).
Verifies token counting and similarity utilities against the specification.
"""
import pytest
import sys
from pathlib import Path

# Ensure src is in path for testing
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data.ablation_utils import calculate_token_count, calculate_similarity

class TestTokenCounting:
    """Tests for calculate_token_count function."""

    def test_token_count_positive(self):
        """Verify that token count is positive for valid text."""
        count = calculate_token_count("test")
        assert count > 0, "Token count must be greater than 0"

    def test_token_count_empty(self):
        """Verify behavior with empty string."""
        count = calculate_token_count("")
        assert count == 0, "Empty string should have 0 tokens"

    def test_token_count_various_lengths(self):
        """Verify token count scales with text length."""
        short = "a"
        long = "a " * 100
        count_short = calculate_token_count(short)
        count_long = calculate_token_count(long)
        assert count_long >= count_short, "Longer text should have >= tokens"

    def test_token_count_list(self):
        """Verify token count works on a list of strings."""
        texts = ["hello", "world"]
        count = calculate_token_count(texts)
        assert count > 0, "List of valid strings must have positive token count"

class TestSimilarity:
    """Tests for calculate_similarity function."""

    def test_identical_strings(self):
        """Verify similarity is 1.0 for identical strings (or close enough)."""
        sim = calculate_similarity("a", "a")
        assert 0 <= sim <= 1, "Similarity must be between 0 and 1"
        # For single identical words, TF-IDF cosine similarity is 1.0
        assert sim == 1.0, f"Identical strings should have similarity 1.0, got {sim}"

    def test_different_strings(self):
        """Verify similarity is lower for different strings."""
        sim = calculate_similarity("cat", "dog")
        assert 0 <= sim <= 1, "Similarity must be between 0 and 1"
        # Should be less than 1.0
        assert sim < 1.0, "Different strings should have similarity < 1.0"

    def test_empty_strings(self):
        """Verify handling of empty strings."""
        sim = calculate_similarity("", "")
        assert sim == 0.0, "Empty strings should have 0 similarity"

    def test_one_empty_string(self):
        """Verify handling when one string is empty."""
        sim = calculate_similarity("text", "")
        assert sim == 0.0, "One empty string should result in 0 similarity"

    def test_similar_contexts(self):
        """Verify similarity captures semantic overlap (e.g., shared words)."""
        # "the cat" and "the dog" share "the"
        sim = calculate_similarity("the cat", "the dog")
        assert 0 <= sim <= 1, "Similarity must be between 0 and 1"
        # Should be non-zero because of shared "the"
        assert sim > 0.0, "Strings sharing words should have non-zero similarity"