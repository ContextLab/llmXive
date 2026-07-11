import pytest
import math
from collections import Counter
from pathlib import Path
import sys

# Add project root to path for imports if running from tests/
if str(Path(__file__).parent.parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.metrics_utils import safe_parse_ast, detect_zero_variance


class TestNGramEntropy:
    """Unit tests for n-gram entropy calculation logic."""

    def _calculate_ngram_entropy(self, text: str, n: int = 2) -> float:
        """
        Helper to calculate n-gram entropy for testing.
        Formula: H = -sum(p(x) * log2(p(x)))
        """
        if not text or len(text) < n:
            return 0.0

        # Extract n-grams
        ngrams = [text[i:i+n] for i in range(len(text) - n + 1)]
        
        if not ngrams:
            return 0.0

        # Calculate probabilities
        counts = Counter(ngrams)
        total = len(ngrams)
        
        entropy = 0.0
        for count in counts.values():
            p = count / total
            if p > 0:
                entropy -= p * math.log2(p)
        
        return entropy

    def test_identical_strings_zero_entropy(self):
        """Identical strings should theoretically have low entropy relative to variation,
        but strictly speaking, a sequence of identical characters has entropy 0.
        Here we test the helper logic: a string of all same characters."""
        text = "aaaa"
        entropy = self._calculate_ngram_entropy(text, n=2)
        # "aa", "aa", "aa" -> 1 unique ngram, p=1.0 -> log2(1)=0 -> entropy=0
        assert entropy == 0.0, f"Expected 0.0 entropy for identical chars, got {entropy}"

    def test_alternating_pattern_higher_entropy(self):
        """Alternating patterns should have higher entropy than identical strings."""
        text_same = "aaaa"
        text_alt = "abab"
        
        ent_same = self._calculate_ngram_entropy(text_same, n=2)
        ent_alt = self._calculate_ngram_entropy(text_alt, n=2)
        
        assert ent_same == 0.0
        assert ent_alt > ent_same, f"Alternating pattern should have higher entropy ({ent_alt}) than identical ({ent_same})"

    def test_empty_string_zero_entropy(self):
        """Empty string should return 0 entropy."""
        entropy = self._calculate_ngram_entropy("", n=2)
        assert entropy == 0.0

    def test_short_string_less_than_n(self):
        """String shorter than n should return 0 entropy."""
        entropy = self._calculate_ngram_entropy("ab", n=5)
        assert entropy == 0.0

    def test_realistic_code_snippet(self):
        """Test with a realistic code snippet to ensure it doesn't crash and returns a float."""
        code = "def foo(x):\n    return x + 1"
        entropy = self._calculate_ngram_entropy(code, n=2)
        assert isinstance(entropy, float)
        assert entropy >= 0.0
        # Real code usually has entropy > 0 due to variety of characters
        assert entropy > 0.0, "Realistic code should have non-zero entropy"

    def test_token_level_entropy(self):
        """Test entropy calculation on tokenized input (space-separated)."""
        tokens = "def foo x return x add 1"
        # Treating space-separated as the "text" for n-gram on tokens
        entropy = self._calculate_ngram_entropy(tokens, n=2)
        assert isinstance(entropy, float)
        assert entropy > 0.0

class TestMetricsIntegration:
    """Integration tests ensuring the metrics_utils module works with the test suite."""

    def test_safe_parse_ast_returns_node(self):
        """Ensure safe_parse_ast correctly parses valid Python code."""
        code = "x = 1"
        tree = safe_parse_ast(code)
        assert tree is not None
        assert isinstance(tree, ast.AST)

    def test_safe_parse_ast_returns_none_for_invalid(self):
        """Ensure safe_parse_ast returns None for invalid code."""
        code = "x = "
        tree = safe_parse_ast(code)
        assert tree is None

    def test_detect_zero_variance_on_list(self):
        """Test zero variance detection on a list of values."""
        # All same values
        values = [1.0, 1.0, 1.0]
        is_zero, msg = detect_zero_variance(values)
        assert is_zero is True
        
        # Different values
        values_diff = [1.0, 2.0, 3.0]
        is_zero_diff, msg_diff = detect_zero_variance(values_diff)
        assert is_zero_diff is False

    def test_detect_zero_variance_empty_list(self):
        """Test zero variance detection on empty list."""
        is_zero, msg = detect_zero_variance([])
        # Usually considered zero variance or undefined, check implementation behavior
        # Based on typical logic: if no variance possible, it's zero.
        assert is_zero is True