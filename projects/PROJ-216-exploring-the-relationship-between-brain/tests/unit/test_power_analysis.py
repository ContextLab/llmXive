import pytest
import sys
import os
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from stats import calculate_power, create_limitations_text, generate_power_analysis_table

class TestPowerAnalysis:
    def test_calculate_power_small_sample(self):
        """Test power calculation with N=10."""
        # For a medium effect size (0.5), power should be low with N=10
        power = calculate_power(0.5, 10)
        assert 0.0 <= power <= 1.0
        # With N=10, power for r=0.5 is typically around 0.18-0.20
        # We just check it's a valid probability
        assert power < 0.5 # Expecting low power for small N

    def test_calculate_power_large_sample(self):
        """Test power calculation with larger N."""
        # With N=100, power for r=0.5 should be much higher
        power = calculate_power(0.5, 100)
        assert 0.0 <= power <= 1.0
        # Should be significantly higher than for N=10
        power_small = calculate_power(0.5, 10)
        assert power > power_small

    def test_calculate_power_zero_effect(self):
        """Test power calculation with zero effect size."""
        power = calculate_power(0.0, 10)
        # Power for zero effect should be near alpha (0.05) or 0 depending on implementation
        # In our implementation, it should be low
        assert power >= 0.0

    def test_create_limitations_text_content(self):
        """Test that limitations text contains required phrases."""
        text = create_limitations_text(10)
        assert "N=10" in text
        assert "low statistical power" in text
        assert "exploratory" in text
        assert "larger cohorts" in text
        assert "UNRESOLVED-CLAIM" in text

    def test_generate_power_analysis_table(self):
        """Test generation of power analysis table."""
        table = generate_power_analysis_table(10)
        assert len(table) > 0
        assert "effect_size" in table[0]
        assert "estimated_power" in table[0]
        assert table[0]["sample_size"] == 10