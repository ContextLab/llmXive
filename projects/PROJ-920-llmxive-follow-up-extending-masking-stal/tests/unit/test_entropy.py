"""
Unit tests for the entropy utility module.

Verifies:
1. Correct Shannon entropy calculation on known inputs.
2. Clamping behavior for out-of-range values.
3. Edge case handling for zero density (empty input, single unique byte).
4. Logging of zero-density events (FR-008).
"""
import math
import logging
import io
import sys
import pytest
from pathlib import Path

# Add project root to path to allow imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.utils.entropy import calculate_shannon_entropy, clamp_entropy, entropy_per_token


class TestCalculateShannonEntropy:
    """Tests for the core entropy calculation function."""

    def test_empty_input_returns_zero(self):
        """Empty string should return 0.0 entropy."""
        assert calculate_shannon_entropy("") == 0.0
        assert calculate_shannon_entropy(b"") == 0.0

    def test_single_character(self):
        """String with one unique character has 0 entropy."""
        text = "aaaaa"
        entropy = calculate_shannon_entropy(text)
        assert entropy == 0.0

    def test_two_character_equal_probability(self):
        """String with two characters of equal frequency has 1.0 bit entropy."""
        # "ab" repeated -> 50% 'a', 50% 'b'
        text = "ab" * 10
        entropy = calculate_shannon_entropy(text)
        # H = - (0.5 * log2(0.5) + 0.5 * log2(0.5)) = 1.0
        assert math.isclose(entropy, 1.0, rel_tol=1e-9)

    def test_known_distribution(self):
        """Test with a known distribution to verify calculation."""
        # 3 'a's, 1 'b' -> total 4
        # p(a) = 0.75, p(b) = 0.25
        text = "aaab"
        entropy = calculate_shannon_entropy(text)
        # H = - (0.75 * log2(0.75) + 0.25 * log2(0.25))
        expected = - (0.75 * math.log2(0.75) + 0.25 * math.log2(0.25))
        assert math.isclose(entropy, expected, rel_tol=1e-9)

    def test_bytes_input(self):
        """Should handle raw bytes input correctly."""
        byte_data = b"\x00\x00\xff\xff\xff"
        # 2 zeros, 3 fives -> p(0)=0.4, p(255)=0.6
        entropy = calculate_shannon_entropy(byte_data)
        expected = - (0.4 * math.log2(0.4) + 0.6 * math.log2(0.6))
        assert math.isclose(entropy, expected, rel_tol=1e-9)

    def test_invalid_type_raises(self):
        """Should raise TypeError for non-str/non-bytes input."""
        with pytest.raises(TypeError):
            calculate_shannon_entropy(123)
        
        with pytest.raises(TypeError):
            calculate_shannon_entropy(None)

    def test_logging_zero_density_empty(self, caplog):
        """Verify that zero density on empty input triggers a warning log."""
        # Capture logs
        with caplog.at_level(logging.WARNING):
            calculate_shannon_entropy("")
        
        assert any("Zero density event" in record.message for record in caplog.records)

    def test_logging_zero_density_single_byte(self, caplog):
        """Verify that zero density on single-unique-byte input triggers a warning log."""
        with caplog.at_level(logging.WARNING):
            calculate_shannon_entropy("zzzzz")
        
        assert any("Zero density event" in record.message for record in caplog.records)


class TestClampEntropy:
    """Tests for the clamping utility."""

    def test_value_within_range_unchanged(self):
        """Values within [min, max] should remain unchanged."""
        assert clamp_entropy(4.5, 0.0, 8.0) == 4.5
        assert clamp_entropy(0.0, 0.0, 8.0) == 0.0
        assert clamp_entropy(8.0, 0.0, 8.0) == 8.0

    def test_value_below_min_clamped(self):
        """Values below min should be clamped to min."""
        assert clamp_entropy(-1.0, 0.0, 8.0) == 0.0
        assert clamp_entropy(-5.5, 2.0, 10.0) == 2.0

    def test_value_above_max_clamped(self):
        """Values above max should be clamped to max."""
        assert clamp_entropy(9.0, 0.0, 8.0) == 8.0
        assert clamp_entropy(15.0, 0.0, 8.0) == 8.0


class TestEntropyPerToken:
    """Tests for the per-token entropy function."""

    def test_default_token_length(self):
        """Default token length (1) should return total entropy."""
        text = "abab"
        total = calculate_shannon_entropy(text)
        per_token = entropy_per_token(text)
        assert math.isclose(total, per_token, rel_tol=1e-9)

    def test_invalid_token_length_raises(self):
        """Token length < 1 should raise ValueError."""
        with pytest.raises(ValueError):
            entropy_per_token("test", token_length=0)
        
        with pytest.raises(ValueError):
            entropy_per_token("test", token_length=-1)

    def test_short_text_returns_zero(self):
        """Text shorter than token_length should return 0.0."""
        # Token length 5, text length 3
        assert entropy_per_token("abc", token_length=5) == 0.0

    def test_logging_short_text(self, caplog):
        """Verify warning log when text is shorter than token length."""
        with caplog.at_level(logging.WARNING):
            entropy_per_token("abc", token_length=5)
        
        assert any("Zero density event" in record.message for record in caplog.records)