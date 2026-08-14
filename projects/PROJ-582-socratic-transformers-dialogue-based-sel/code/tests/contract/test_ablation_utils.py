"""
Contract tests for ablation_utils module.

These tests verify the correctness of the syntactic complexity calculator
and token length functions.
"""
import pytest
from pathlib import Path
import sys

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.data.ablation_utils import calculate_syntactic_complexity, calculate_token_length


class TestSyntacticComplexityCalculator:
    """Tests for the calculate_syntactic_complexity function."""

    def test_empty_string(self):
        """Test that empty string returns zero complexity."""
        result = calculate_syntactic_complexity("")
        assert result["token_count"] == 0.0
        assert result["ngram_entropy"] == 0.0

    def test_single_word(self):
        """Test complexity calculation for a single word."""
        result = calculate_syntactic_complexity("hello")
        assert result["token_count"] > 0
        # Single word should have low entropy
        assert result["ngram_entropy"] >= 0.0

    def test_repeated_text(self):
        """Test that repeated text has lower entropy."""
        simple_text = "the the the the the"
        complex_text = "the quick brown fox jumps over the lazy dog"
        
        simple_complexity = calculate_syntactic_complexity(simple_text)
        complex_complexity = calculate_syntactic_complexity(complex_text)
        
        # Simple repeated text should have lower entropy
        assert simple_complexity["ngram_entropy"] <= complex_complexity["ngram_entropy"]

    def test_token_count_increases_with_length(self):
        """Test that token count increases with text length."""
        short_text = "hello world"
        long_text = "hello world " * 10
        
        short_complexity = calculate_syntactic_complexity(short_text)
        long_complexity = calculate_syntactic_complexity(long_text)
        
        assert long_complexity["token_count"] > short_complexity["token_count"]

    def test_returns_dict_with_correct_keys(self):
        """Test that the function returns a dictionary with required keys."""
        result = calculate_syntactic_complexity("test text")
        assert "token_count" in result
        assert "ngram_entropy" in result
        assert isinstance(result["token_count"], float)
        assert isinstance(result["ngram_entropy"], float)


class TestTokenLengthCalculator:
    """Tests for the calculate_token_length function."""

    def test_empty_string(self):
        """Test that empty string has zero tokens."""
        result = calculate_token_length("")
        assert result == 0

    def test_single_word(self):
        """Test token count for a single word."""
        result = calculate_token_length("hello")
        assert result > 0

    def test_space_separated_words(self):
        """Test that space-separated words are counted correctly."""
        result = calculate_token_length("hello world")
        assert result > 1

    def test_consistency_with_complexity(self):
        """Test that token length matches the token_count from complexity function."""
        text = "This is a test sentence for token counting."
        
        length = calculate_token_length(text)
        complexity = calculate_syntactic_complexity(text)
        
        assert length == complexity["token_count"]