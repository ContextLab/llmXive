import pytest
import sys
import os
from pathlib import Path
import math

# Add code to path if running standalone
code_path = Path(__file__).parent.parent.parent / "code"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

from data.compute_features import compute_entropy, is_ambiguous_token, compute_kenlm_perplexity, compute_local_semantic_density

class TestComputeEntropy:
    def test_compute_entropy_uniform(self):
        """Test entropy with uniform distribution (should be log2(2) = 1.0 for binary)"""
        # Input: "ab" -> 1 'a', 1 'b' -> probs [0.5, 0.5] -> entropy 1.0
        text = "ab"
        result = compute_entropy(list(text))
        assert abs(result - 1.0) < 1e-5

    def test_compute_entropy_deterministic(self):
        """Test entropy with deterministic distribution (should be 0)"""
        # Input: "aaaa" -> 4 'a' -> probs [1.0] -> entropy 0.0
        text = "aaaa"
        result = compute_entropy(list(text))
        assert result == 0.0

    def test_compute_entropy_empty(self):
        """Test entropy with empty input"""
        result = compute_entropy([])
        assert result == 0.0

class TestIsAmbiguousToken:
    def test_standard_token(self):
        """Standard alphanumeric token should not be ambiguous"""
        info = is_ambiguous_token("hello")
        assert info["is_ambiguous"] is False
        assert info["category"] == "neutral"

    def test_special_char(self):
        """Special characters should be detected"""
        info = is_ambiguous_token("$$$")
        assert info["is_ambiguous"] is True
        assert info["category"] == "special"

    def test_emoji(self):
        """Emojis should be detected"""
        info = is_ambiguous_token("🚀")
        assert info["is_ambiguous"] is True
        assert info["category"] == "emoji"
        
        info_multi = is_ambiguous_token("Hello 🚀")
        assert info_multi["is_ambiguous"] is True
        assert info_multi["category"] == "emoji"

    def test_control_char(self):
        """Control characters should be detected"""
        info = is_ambiguous_token("\x00")
        assert info["is_ambiguous"] is True
        assert info["category"] == "control"

    def test_empty_token(self):
        """Empty token should be handled gracefully"""
        info = is_ambiguous_token("")
        assert info["is_ambiguous"] is True
        assert info["category"] == "control" # Or specific empty category

    def test_punctuation(self):
        """Standard punctuation should be neutral"""
        info = is_ambiguous_token(".")
        assert info["is_ambiguous"] is False
        assert info["category"] == "neutral"

class TestComputeKenlmPerplexity:
    def test_compute_kenlm_perplexity_empty(self):
        """Test that empty input returns infinity or handles gracefully"""
        # Since kenlm might not be installed, we test the logic flow
        result = compute_kenlm_perplexity("", None)
        assert math.isinf(result)

class TestLocalSemanticDensity:
    def test_density_calculation(self):
        """Test density calculation with known inputs"""
        tokens = ["a", "b", "c", "d", "e"]
        # Window around index 2 ('c') with size 1 -> ["b", "c", "d"]
        # Trigrams: (b, c, d) -> 1 unique, 1 total -> density 1.0
        density = compute_local_semantic_density(tokens, center_idx=2, window_size=1)
        assert density == 1.0

    def test_density_duplicates(self):
        """Test density with duplicate trigrams"""
        tokens = ["a", "a", "a", "a", "a"]
        # Window around index 2 -> ["a", "a", "a"]
        # Trigrams: (a, a, a) -> 1 unique, 1 total -> density 1.0
        # Actually, if window is larger:
        # Let's try window_size=2 -> ["a", "a", "a", "a"]
        # Trigrams: (a,a,a), (a,a,a) -> 1 unique, 2 total -> 0.5
        density = compute_local_semantic_density(tokens, center_idx=2, window_size=2)
        assert density == 0.5

    def test_density_insufficient_tokens(self):
        """Test density when window has fewer than 3 tokens"""
        tokens = ["a", "b"]
        density = compute_local_semantic_density(tokens, center_idx=0, window_size=1)
        assert density == 0.0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])