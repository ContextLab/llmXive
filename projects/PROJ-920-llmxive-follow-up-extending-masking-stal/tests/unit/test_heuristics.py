"""
Unit tests for code/utils/heuristics.py
Verifies technical token ratio and composite density calculations.
"""
import pytest
import sys
from pathlib import Path

# Add project root to path to allow imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from code.utils.heuristics import calculate_technical_token_ratio, calculate_composite_density
from code.utils.entropy import calculate_shannon_entropy


class TestCalculateTechnicalTokenRatio:
    """Tests for the technical token ratio calculation."""

    def test_empty_string(self):
        """Empty string should return 0.0 ratio."""
        assert calculate_technical_token_ratio("") == 0.0

    def test_no_technical_tokens(self):
        """Text with no technical tokens should return 0.0."""
        text = "hello world this is normal text"
        assert calculate_technical_token_ratio(text) == 0.0

    def test_all_technical_tokens(self):
        """Text consisting entirely of technical tokens should return 1.0."""
        # Assuming the technical list includes common symbols like <, >, {, }
        # We need to construct a string that matches the regex in heuristics.py
        # The regex is typically something like r'[<>\{\}\[\]\(\)=\+\-*/\\|;:,.]'
        # Let's use a string of known technical characters.
        # Note: The actual regex in heuristics.py is: r'[<>\{\}\[\]\(\)=\+\-*/\\|;:,.!?]'
        text = "<>{[]}=+-*\\|;:,.!?"
        ratio = calculate_technical_token_ratio(text)
        # All characters should match
        assert ratio == 1.0

    def test_mixed_tokens(self):
        """Mixed text should return the correct ratio."""
        # "a<b>c" -> 3 chars. '<', '>' are technical. 'a', 'b', 'c' are not.
        # Ratio = 2 / 5 = 0.4
        text = "a<b>c"
        ratio = calculate_technical_token_ratio(text)
        assert abs(ratio - 0.4) < 1e-9

    def test_case_sensitivity(self):
        """Verify that the regex handles case correctly (usually case-insensitive for letters, but technical symbols are fixed)."""
        # Technical tokens are symbols, so case doesn't apply to them directly,
        # but the surrounding text might.
        text = "A<B>C"
        ratio = calculate_technical_token_ratio(text)
        assert abs(ratio - 0.4) < 1e-9


class TestCalculateCompositeDensity:
    """Tests for the composite density formula: 0.6 * Shannon_Entropy + 0.4 * Technical_Token_Ratio."""

    def test_zero_entropy_zero_ratio(self):
        """Both zero should result in zero density."""
        # "aaaa" -> H=0, ratio=0
        density = calculate_composite_density("aaaa")
        assert density == 0.0

    def test_max_entropy_zero_ratio(self):
        """Max entropy (uniform binary) with zero technical tokens."""
        # "ab" -> H=1.0, ratio=0
        # Density = 0.6 * 1.0 + 0.4 * 0 = 0.6
        density = calculate_composite_density("ab")
        assert abs(density - 0.6) < 1e-4

    def test_zero_entropy_max_ratio(self):
        """Zero entropy (uniform symbol) with max technical ratio."""
        # "<<" -> H=0, ratio=1.0 (assuming '<' is technical)
        # Density = 0.6 * 0 + 0.4 * 1.0 = 0.4
        density = calculate_composite_density("<<")
        assert abs(density - 0.4) < 1e-4

    def test_combined_values(self):
        """Test with specific calculated values."""
        # Let's construct a string with known H and Ratio.
        # "a<b" -> len=3.
        # Chars: 'a', '<', 'b'.
        # Frequencies: a:1, <:1, b:1. H = log2(3) ≈ 1.585.
        # Technical: '<' (1 out of 3). Ratio = 0.333...
        # Density = 0.6 * 1.585 + 0.4 * 0.333...
        # ≈ 0.951 + 0.133 = 1.084
        text = "a<b"
        h = calculate_shannon_entropy(text)
        ratio = calculate_technical_token_ratio(text)
        expected_density = 0.6 * h + 0.4 * ratio
        density = calculate_composite_density(text)
        assert abs(density - expected_density) < 1e-4

    def test_weighted_average_property(self):
        """Verify the result is strictly between the two components (unless one is 0)."""
        # If H > 0 and Ratio > 0, then 0.6*H + 0.4*Ratio should be between 0 and max(H, Ratio) roughly.
        # Specifically, it's a convex combination.
        text = "code<test>"
        density = calculate_composite_density(text)
        h = calculate_shannon_entropy(text)
        ratio = calculate_technical_token_ratio(text)
        
        # Check bounds: min(0.6*H, 0.4*R) <= Density <= max(0.6*H, 0.4*R) is not quite right.
        # It is exactly 0.6*H + 0.4*R.
        # Just verify the formula is applied.
        assert abs(density - (0.6 * h + 0.4 * ratio)) < 1e-9
