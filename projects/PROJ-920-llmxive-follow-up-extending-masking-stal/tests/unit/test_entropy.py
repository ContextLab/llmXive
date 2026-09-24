"""
Unit tests for entropy.py utility functions.
Verifies Shannon entropy calculation, clamping for zero density, and logging behavior.
"""
import math
import logging
import sys
import os
from io import StringIO
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from utils.entropy import calculate_shannon_entropy, clamp_entropy, entropy_per_token


class TestCalculateShannonEntropy:
    """Tests for the calculate_shannon_entropy function."""

    def test_empty_string_returns_zero(self):
        """Empty input should return 0.0 entropy."""
        result = calculate_shannon_entropy("")
        assert result == 0.0

    def test_single_char_returns_zero(self):
        """Single character string has 0 entropy (only one possible outcome)."""
        result = calculate_shannon_entropy("a")
        assert result == 0.0

    def test_uniform_distribution(self):
        """Uniform distribution of characters should yield high entropy."""
        # "ab" repeated: uniform distribution between 'a' and 'b'
        text = "ab" * 10
        result = calculate_shannon_entropy(text)
        # Max entropy for 2 symbols is log2(2) = 1.0
        assert math.isclose(result, 1.0, rel_tol=1e-5)

    def test_skewed_distribution(self):
        """Skewed distribution should yield lower entropy."""
        # Mostly 'a', few 'b's
        text = "a" * 90 + "b" * 10
        result = calculate_shannon_entropy(text)
        # Should be less than 1.0
        assert result < 1.0
        assert result > 0.0

    def test_utf8_byte_level(self):
        """Function should operate on UTF-8 byte level."""
        # Non-ASCII character
        text = "café"
        result = calculate_shannon_entropy(text)
        assert result > 0.0


class TestClampEntropy:
    """Tests for the clamp_entropy function."""

    def test_zero_density_clamped(self):
        """Zero density value should be clamped to a small positive value."""
        result = clamp_entropy(0.0)
        assert result > 0.0
        # Default epsilon is 1e-8
        assert result == 1e-8

    def test_custom_epsilon(self):
        """Custom epsilon should be used for clamping."""
        result = clamp_entropy(0.0, epsilon=1e-5)
        assert result == 1e-5

    def test_non_zero_unchanged(self):
        """Non-zero values should remain unchanged."""
        original = 0.5
        result = clamp_entropy(original)
        assert result == original

    def test_negative_value_clamped(self):
        """Negative values (if any) should be clamped."""
        result = clamp_entropy(-0.5)
        assert result == 1e-8


class TestEntropyPerToken:
    """Tests for the entropy_per_token function."""

    def test_zero_byte_count_clamped(self):
        """Zero byte count should trigger clamping and return 0.0."""
        result = entropy_per_token("", 0)
        assert result == 0.0

    def test_normal_calculation(self):
        """Normal case: entropy divided by token count."""
        text = "hello world"
        # Calculate entropy manually
        entropy_val = calculate_shannon_entropy(text)
        # Token count is len(text) in bytes for this implementation
        tokens = len(text.encode('utf-8'))
        result = entropy_per_token(text, tokens)
        expected = entropy_val / tokens
        assert math.isclose(result, expected, rel_tol=1e-5)

    def test_logging_on_zero_density(self):
        """Zero density events should be logged."""
        # Capture log output
        log_stream = StringIO()
        handler = logging.StreamHandler(log_stream)
        handler.setLevel(logging.WARNING)
        
        logger = logging.getLogger('utils.entropy')
        logger.addHandler(handler)
        logger.setLevel(logging.WARNING)

        # Trigger zero density
        result = entropy_per_token("", 0)
        
        # Check that a warning was logged
        log_output = log_stream.getvalue()
        assert "Zero density" in log_output or "clamped" in log_output.lower()

        # Cleanup
        logger.removeHandler(handler)

    def test_clamping_applied(self):
        """Verify that clamping is applied when density is zero."""
        result = entropy_per_token("", 0)
        # Should return 0.0 as defined in the spec for zero density
        assert result == 0.0
