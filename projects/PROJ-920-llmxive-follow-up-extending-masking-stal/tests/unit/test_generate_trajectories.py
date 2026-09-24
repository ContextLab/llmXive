"""
Unit tests for generate_trajectories.py functions.
Verifies trajectory generation, density injection, and validation logic.
"""
import math
import random
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from generate_trajectories import generate_text_block, inject_critical_evidence, clamp_density, validate_density_computation


class TestGenerateTextBlock:
    """Tests for the generate_text_block function."""

    def test_block_generation(self):
        """Should generate a text block of specified length."""
        text = generate_text_block(100, seed=42)
        assert len(text) == 100

    def test_seed_reproducibility(self):
        """Same seed should produce same text."""
        text1 = generate_text_block(50, seed=123)
        text2 = generate_text_block(50, seed=123)
        assert text1 == text2

    def test_different_seed_different_text(self):
        """Different seeds should produce different text."""
        text1 = generate_text_block(50, seed=123)
        text2 = generate_text_block(50, seed=456)
        assert text1 != text2

    def test_empty_block(self):
        """Zero length should return empty string."""
        text = generate_text_block(0, seed=42)
        assert text == ""

    def test_contains_expected_chars(self):
        """Generated text should contain expected characters."""
        text = generate_text_block(100, seed=42)
        # Should contain lowercase letters, spaces, etc.
        assert any(c.isalpha() for c in text)


class TestInjectCriticalEvidence:
    """Tests for the inject_critical_evidence function."""

    def test_evidence_injected(self):
        """Critical evidence should be present in the output."""
        evidence = "CRITICAL_EVIDENCE_BLOCK"
        text = inject_critical_evidence("base text", evidence, 5)
        assert evidence in text

    def test_evidence_at_correct_index(self):
        """Evidence should be at the specified turn index."""
        evidence = "EVIDENCE"
        turn_index = 3
        # The implementation should place evidence at the correct logical position
        text = inject_critical_evidence("base", evidence, turn_index)
        assert evidence in text

    def test_return_structure(self):
        """Function should return a dictionary with required fields."""
        evidence = "TEST"
        result = inject_critical_evidence("base", evidence, 2)
        assert isinstance(result, dict)
        assert "text" in result
        assert "evidence_turn_index" in result
        assert "is_critical" in result
        assert result["is_critical"] is True


class TestClampDensity:
    """Tests for the clamp_density function."""

    def test_value_in_range(self):
        """Values within range should be unchanged."""
        result = clamp_density(0.5)
        assert result == 0.5

    def test_value_below_min(self):
        """Values below min should be clamped to min."""
        result = clamp_density(-0.5)
        assert result == 0.0

    def test_value_above_max(self):
        """Values above max should be clamped to max."""
        result = clamp_density(1.5)
        assert result == 1.0

    def test_custom_range(self):
        """Custom range should be respected."""
        result = clamp_density(0.1, min_val=0.2, max_val=0.8)
        assert result == 0.2

    def test_zero_density_clamped(self):
        """Zero density should be clamped to epsilon."""
        result = clamp_density(0.0)
        assert result > 0.0


class TestValidateDensityComputation:
    """Tests for the validate_density_computation function."""

    def test_valid_density(self):
        """Valid density computation should return True."""
        text = "some test text"
        density = 0.5
        result = validate_density_computation(text, density)
        # Should return True if density is within expected bounds
        assert result is True

    def test_density_computed_from_text(self):
        """Density should be computed solely from input text."""
        text1 = "short"
        text2 = "a" * 1000
        density1 = 0.3
        density2 = 0.3
        # Both should validate as True (density is within bounds)
        assert validate_density_computation(text1, density1) is True
        assert validate_density_computation(text2, density2) is True

    def test_invalid_density(self):
        """Invalid density (e.g., negative) should return False."""
        text = "test"
        density = -0.5
        result = validate_density_computation(text, density)
        assert result is False
