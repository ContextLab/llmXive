"""
Unit tests for power analysis functions in stats.py.
"""
import pytest
import math
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stats import calculate_power, generate_power_analysis_table, create_limitations_text

class TestPowerAnalysis:
    def test_calculate_power_small_sample(self):
        """Test power calculation with small sample size (N=10)."""
        # With N=10, even a large effect size should have low power
        power = calculate_power(n=10, effect_size=0.5)
        assert 0.0 <= power <= 1.0
        # We expect low power for N=10
        assert power < 0.8

    def test_calculate_power_large_sample(self):
        """Test power calculation with large sample size."""
        # With N=100, a moderate effect size should have high power
        power = calculate_power(n=100, effect_size=0.5)
        assert 0.0 <= power <= 1.0
        assert power > 0.8

    def test_calculate_power_effect_size_zero(self):
        """Test power calculation with zero effect size."""
        power = calculate_power(n=10, effect_size=0.0)
        # Power should be equal to alpha (type I error rate) if effect is zero
        # But our approximation might return a small value
        assert 0.0 <= power <= 0.1

    def test_generate_power_analysis_table(self):
        """Test generation of power analysis table."""
        effect_sizes = [0.1, 0.3, 0.5]
        table = generate_power_analysis_table(effect_sizes, n=10)
        
        assert len(table) == 3
        for row in table:
            assert 'effect_size' in row
            assert 'sample_size' in row
            assert 'estimated_power' in row
            assert row['sample_size'] == 10
            assert 0.0 <= row['estimated_power'] <= 1.0

    def test_create_limitations_text(self):
        """Test creation of limitations text."""
        power_results = [{'effect_size': 0.5, 'estimated_power': 0.5}]
        text = create_limitations_text(n=10, power_results=power_results)
        
        assert "Limitations" in text
        assert "N=10" in text
        assert "Statistical Power" in text
        assert "exploratory" in text

    def test_calculate_power_edge_cases(self):
        """Test edge cases for power calculation."""
        # Effect size = 1.0
        power = calculate_power(n=10, effect_size=1.0)
        assert power == 1.0

        # Effect size > 1.0
        power = calculate_power(n=10, effect_size=1.5)
        assert power == 1.0

        # Very small sample
        power = calculate_power(n=2, effect_size=0.5)
        assert 0.0 <= power <= 1.0