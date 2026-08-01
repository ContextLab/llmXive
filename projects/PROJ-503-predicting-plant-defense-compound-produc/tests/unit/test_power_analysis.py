"""
Unit tests for power analysis module.

Tests for T008: Power analysis on final paired set.
Verifies power calculations and abort criteria.
"""
import pytest
import json
import math
from pathlib import Path
import sys
import os

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from power_analysis import (
    calculate_z_score,
    calculate_required_n,
    calculate_power,
    run_power_analysis
)
from exceptions import E_POWER


class TestCalculateZScore:
    """Tests for Fisher's z-transformation."""
    
    def test_standard_effect_size(self):
        """Test z-score calculation for r=0.5"""
        z = calculate_z_score(0.5)
        # Fisher's z for r=0.5 is approximately 0.549
        expected = 0.5 * math.log((1 + 0.5) / (1 - 0.5))
        assert abs(z - expected) < 1e-10
        
    def test_small_effect_size(self):
        """Test z-score for small effect size"""
        z = calculate_z_score(0.1)
        expected = 0.5 * math.log((1 + 0.1) / (1 - 0.1))
        assert abs(z - expected) < 1e-10
        
    def test_invalid_effect_size(self):
        """Test that effect size >= 1 raises error"""
        with pytest.raises(ValueError):
            calculate_z_score(1.0)
        with pytest.raises(ValueError):
            calculate_z_score(-1.0)


class TestCalculateRequiredN:
    """Tests for sample size calculation."""
    
    def test_medium_effect_size(self):
        """Test N calculation for effect_size=0.5, alpha=0.05, power=0.8"""
        n = calculate_required_n(effect_size=0.5, alpha=0.05, power=0.8)
        # Expected N is approximately 29 for these parameters
        assert n >= 25 and n <= 35
        
    def test_large_effect_size(self):
        """Test N calculation for large effect size"""
        n = calculate_required_n(effect_size=0.8, alpha=0.05, power=0.8)
        # Larger effect size should require smaller N
        assert n < 20
        
    def test_high_power_requirement(self):
        """Test N calculation with higher power requirement"""
        n_low = calculate_required_n(effect_size=0.5, alpha=0.05, power=0.8)
        n_high = calculate_required_n(effect_size=0.5, alpha=0.05, power=0.9)
        # Higher power should require larger N
        assert n_high > n_low
        
    def test_invalid_parameters(self):
        """Test that invalid parameters raise errors"""
        with pytest.raises(ValueError):
            calculate_required_n(effect_size=1.5)
        with pytest.raises(ValueError):
            calculate_required_n(effect_size=0.5, alpha=1.5)
        with pytest.raises(ValueError):
            calculate_required_n(effect_size=0.5, power=1.5)


class TestCalculatePower:
    """Tests for power calculation."""
    
    def test_medium_sample_size(self):
        """Test power calculation for N=40, effect_size=0.5"""
        power = calculate_power(n=40, effect_size=0.5, alpha=0.05)
        # Power should be > 0.8 for these parameters
        assert power > 0.75
        
    def test_small_sample_size(self):
        """Test power calculation for small N"""
        power = calculate_power(n=10, effect_size=0.5, alpha=0.05)
        # Power should be low for small N
        assert power < 0.5
        
    def test_large_sample_size(self):
        """Test power calculation for large N"""
        power = calculate_power(n=100, effect_size=0.5, alpha=0.05)
        # Power should be very high
        assert power > 0.95
        
    def test_very_small_n(self):
        """Test that very small N returns 0 power"""
        power = calculate_power(n=2, effect_size=0.5, alpha=0.05)
        assert power == 0.0


class TestRunPowerAnalysis:
    """Tests for the main power analysis function."""
    
    def test_successful_analysis(self):
        """Test successful power analysis with sufficient N"""
        result = run_power_analysis(
            n_samples=50,
            effect_size=0.5,
            alpha=0.05,
            target_power=0.8,
            min_viable_n=40
        )
        
        assert result["N"] == 50
        assert result["effect_size"] == 0.5
        assert result["alpha"] == 0.05
        assert result["test_type"] == "F-test (correlation)"
        assert result["meets_minimum_viable"] is True
        assert "power" in result
        assert "required_n_for_target" in result
        
    def test_below_minimum_viable(self):
        """Test that E-POWER is raised when N < min_viable_n"""
        with pytest.raises(E_POWER) as exc_info:
            run_power_analysis(
                n_samples=30,
                effect_size=0.5,
                alpha=0.05,
                target_power=0.8,
                min_viable_n=40
            )
        
        assert "E-POWER" in str(exc_info.value)
        assert "30" in str(exc_info.value)
        assert "40" in str(exc_info.value)
        
    def test_below_target_power_warning(self):
        """Test that low power triggers warning but not abort if N >= min"""
        # Use a very small effect size to get low power even with N=40
        result = run_power_analysis(
            n_samples=40,
            effect_size=0.2,
            alpha=0.05,
            target_power=0.8,
            min_viable_n=40
        )
        
        assert result["meets_minimum_viable"] is True
        # Power should be low for small effect size
        assert result["meets_target_power"] is False
        
    def test_output_schema(self):
        """Test that result contains all required fields"""
        result = run_power_analysis(n_samples=50)
        
        required_fields = [
            "N", "power", "effect_size", "alpha", "test_type"
        ]
        for field in required_fields:
            assert field in result, f"Missing required field: {field}"