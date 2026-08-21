"""
Unit tests for code/utils/entropy.py
Verifies Shannon entropy calculation, clamping for zero density, and edge cases.
"""
import pytest
import math
import sys
from pathlib import Path

# Add project root to path to allow imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from code.utils.entropy import calculate_shannon_entropy, clamp_entropy, entropy_per_token


class TestCalculateShannonEntropy:
    """Tests for the core Shannon entropy calculation."""

    def test_empty_string_returns_zero(self):
        """Empty input should return 0 entropy."""
        assert calculate_shannon_entropy("") == 0.0

    def test_single_character_returns_zero(self):
        """A single unique character has 0 entropy (probability 1)."""
        assert calculate_shannon_entropy("a") == 0.0

    def test_uniform_distribution(self):
        """Uniform distribution of characters should have max entropy for that alphabet size."""
        # "ab" -> p(a)=0.5, p(b)=0.5 -> H = - (0.5*log2(0.5) + 0.5*log2(0.5)) = 1.0
        assert calculate_shannon_entropy("ab") == 1.0
        # "aabb" -> same probabilities
        assert calculate_shannon_entropy("aabb") == 1.0

    def test_known_distribution(self):
        """Test with a known distribution: 'a' (75%), 'b' (25%)."""
        # H = - (0.75 * log2(0.75) + 0.25 * log2(0.25))
        # H ≈ - (0.75 * -0.415 + 0.25 * -2.0) ≈ 0.811278
        text = "aaab"
        expected = - (0.75 * math.log2(0.75) + 0.25 * math.log2(0.25))
        result = calculate_shannon_entropy(text)
        assert math.isclose(result, expected, rel_tol=1e-4)

    def test_utf8_bytes(self):
        """Ensure UTF-8 multi-byte characters are handled correctly."""
        # "café" -> bytes: 99, 97, 102, 195, 169 (assuming UTF-8)
        # We treat the byte stream as the token set.
        text = "café"
        result = calculate_shannon_entropy(text)
        assert result > 0.0
        assert not math.isinf(result)


class TestClampEntropy:
    """Tests for the entropy clamping logic (Edge Case: Zero Density)."""

    def test_positive_value_unchanged(self):
        """Positive entropy values should remain unchanged."""
        assert clamp_entropy(1.5) == 1.5
        assert clamp_entropy(0.001) == 0.001

    def test_zero_value_clamped(self):
        """Zero entropy should be clamped to a small epsilon to avoid division by zero later."""
        epsilon = 1e-9
        result = clamp_entropy(0.0)
        assert result == epsilon

    def test_negative_value_clamped(self):
        """Negative entropy (theoretical error) should be clamped to epsilon."""
        epsilon = 1e-9
        result = clamp_entropy(-0.5)
        assert result == epsilon


class TestEntropyPerToken:
    """Tests for entropy normalized by token (byte) count."""

    def test_empty_string(self):
        """Empty string should return 0."""
        assert entropy_per_token("") == 0.0

    def test_single_char(self):
        """Single char: entropy 0, length 1 -> 0."""
        assert entropy_per_token("a") == 0.0

    def test_uniform_ab(self):
        """'ab' -> H=1.0, len=2 -> 0.5."""
        # H("ab") = 1.0
        # Tokens = 2
        # Result = 0.5
        result = entropy_per_token("ab")
        assert math.isclose(result, 0.5, rel_tol=1e-4)

    def test_large_uniform(self):
        """Large string with uniform distribution."""
        # 100 'a's and 100 'b's
        text = "a" * 100 + "b" * 100
        # H = 1.0
        # Length = 200
        # Result = 0.005
        result = entropy_per_token(text)
        assert math.isclose(result, 1.0 / 200.0, rel_tol=1e-4)

    def test_clamping_applied(self):
        """Verify that clamping is applied before division if entropy is 0."""
        # If entropy is 0, clamp_entropy returns 1e-9.
        # 1e-9 / 1 = 1e-9.
        result = entropy_per_token("aaaa")
        # H("aaaa") = 0. Clamped to 1e-9.
        assert result == 1e-9
