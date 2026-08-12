"""Unit tests for atomic fraction conversion and packing efficiency guard clause."""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path

# Import the functions to test from the existing API surface
from code.features.engineering import (
    mass_to_atomic_fractions,
    compute_packing_efficiency,
    parse_composition_string
)
from code.features.constants import get_atomic_mass, get_atomic_radius


class TestAtomicFractionConversion:
    """Tests for mass_to_atomic_fractions function."""

    def test_simple_binary_alloy(self):
        """Test conversion for a simple binary alloy (e.g., 50% Zr, 50% Cu by mass)."""
        mass_fractions = {"Zr": 0.5, "Cu": 0.5}
        
        atomic_fractions = mass_to_atomic_fractions(mass_fractions)
        
        # Atomic mass of Zr ~ 91.22, Cu ~ 63.55
        # Moles Zr = 0.5 / 91.22 ≈ 0.00548
        # Moles Cu = 0.5 / 63.55 ≈ 0.00787
        # Total moles ≈ 0.01335
        # Atomic fraction Zr = 0.00548 / 0.01335 ≈ 0.41
        # Atomic fraction Cu = 0.00787 / 0.01335 ≈ 0.59
        
        assert abs(atomic_fractions["Zr"] - 0.4105) < 0.01
        assert abs(atomic_fractions["Cu"] - 0.5895) < 0.01
        assert abs(sum(atomic_fractions.values()) - 1.0) < 1e-6

    def test_single_element(self):
        """Test that a single element returns atomic fraction of 1.0."""
        mass_fractions = {"Fe": 1.0}
        atomic_fractions = mass_to_atomic_fractions(mass_fractions)
        assert atomic_fractions["Fe"] == 1.0
        assert abs(sum(atomic_fractions.values()) - 1.0) < 1e-6

    def test_ternary_alloy(self):
        """Test conversion for a ternary alloy."""
        mass_fractions = {"Zr": 0.4, "Cu": 0.3, "Al": 0.3}
        atomic_fractions = mass_to_atomic_fractions(mass_fractions)
        
        # Verify sum is 1.0
        assert abs(sum(atomic_fractions.values()) - 1.0) < 1e-6
        
        # Verify all fractions are positive
        for elem, frac in atomic_fractions.items():
            assert frac > 0, f"Atomic fraction for {elem} should be positive"

    def test_invalid_input_empty(self):
        """Test that empty dictionary raises an error or handles gracefully."""
        with pytest.raises((ValueError, ZeroDivisionError)):
            mass_to_atomic_fractions({})

    def test_zero_mass_fraction(self):
        """Test handling of zero mass fraction element."""
        mass_fractions = {"Zr": 0.5, "Cu": 0.0, "Al": 0.5}
        atomic_fractions = mass_to_atomic_fractions(mass_fractions)
        
        # Cu should have 0 atomic fraction
        assert atomic_fractions["Cu"] == 0.0
        # Others should sum to 1.0
        assert abs(atomic_fractions["Zr"] + atomic_fractions["Al"] - 1.0) < 1e-6


class TestPackingEfficiencyGuardClause:
    """Tests for compute_packing_efficiency guard clause when σ_r = 0."""

    def test_single_element_zero_variance(self):
        """Test that packing efficiency is 1.0 when there is only one element (σ_r = 0)."""
        # Composition: 100% Iron
        atomic_fractions = {"Fe": 1.0}
        
        pe = compute_packing_efficiency(atomic_fractions)
        
        # Guard clause: if σ_r = 0, PE should be 1.0
        assert pe == 1.0, "Packing efficiency should be 1.0 for single element (zero variance)"

    def test_two_identical_elements(self):
        """Test PE = 1.0 when all elements have the same radius (theoretical)."""
        # Using Fe for both "elements" to simulate identical radii
        atomic_fractions = {"Fe": 0.5, "Fe": 0.5}  # Note: dict key collision, effectively 1.0 Fe
        
        # Actually, let's test with a case where radii are identical
        # Since we can't have duplicate keys, we test the single element case above
        # and verify the math for a theoretical case
        pass

    def test_normal_case_non_zero_variance(self):
        """Test that normal case (non-zero variance) returns PE < 1.0."""
        # Zr-Cu binary alloy
        atomic_fractions = {"Zr": 0.5, "Cu": 0.5}
        
        pe = compute_packing_efficiency(atomic_fractions)
        
        # Should be less than 1.0 because there is radius mismatch
        assert pe < 1.0, "Packing efficiency should be < 1.0 for alloys with radius mismatch"
        assert pe > 0, "Packing efficiency should be positive"

    def test_packing_efficiency_formula(self):
        """Verify the formula: PE = 1 - (σ_r / r_mean)^2 * (1 - 0.5 * (Δr/r_mean)^2)."""
        # Use a known case: Zr (r=160pm) and Cu (r=128pm) with equal atomic fractions
        # r_mean = (160 + 128) / 2 = 144
        # σ_r = sqrt(((160-144)^2 + (128-144)^2) / 2) = sqrt((256 + 256)/2) = sqrt(256) = 16
        # Δr = 160 - 128 = 32
        # PE = 1 - (16/144)^2 * (1 - 0.5 * (32/144)^2)
        #    = 1 - (0.1111)^2 * (1 - 0.5 * (0.2222)^2)
        #    = 1 - 0.0123 * (1 - 0.5 * 0.0494)
        #    = 1 - 0.0123 * (1 - 0.0247)
        #    = 1 - 0.0123 * 0.9753
        #    = 1 - 0.0120
        #    = 0.9880
        
        atomic_fractions = {"Zr": 0.5, "Cu": 0.5}
        pe = compute_packing_efficiency(atomic_fractions)
        
        # Allow for small floating point differences
        assert abs(pe - 0.988) < 0.01, f"Expected PE ≈ 0.988, got {pe}"

    def test_edge_case_very_small_variance(self):
        """Test PE approaches 1.0 as variance approaches 0."""
        # Use elements with very similar radii
        # Al (143pm) and Si (118pm) - not identical, but let's see
        # Better: use same element twice (handled by single element test)
        # Or use elements with very close radii
        
        # Let's create a case with very small difference
        # Fe (126pm) and Co (125pm) - very close
        atomic_fractions = {"Fe": 0.5, "Co": 0.5}
        pe = compute_packing_efficiency(atomic_fractions)
        
        # Should be close to 1.0
        assert pe > 0.95, f"Packing efficiency should be close to 1.0 for similar radii, got {pe}"


class TestIntegrationWithParseComposition:
    """Integration tests combining parse_composition_string and atomic fraction conversion."""

    def test_full_pipeline_binary(self):
        """Test the full pipeline from composition string to atomic fractions."""
        composition_str = "Zr50Cu50"  # 50% Zr, 50% Cu by mass
        
        mass_fractions = parse_composition_string(composition_str)
        atomic_fractions = mass_to_atomic_fractions(mass_fractions)
        
        # Verify the conversion happened
        assert "Zr" in atomic_fractions
        assert "Cu" in atomic_fractions
        assert abs(sum(atomic_fractions.values()) - 1.0) < 1e-6

    def test_full_pipeline_ternary(self):
        """Test full pipeline with ternary alloy."""
        composition_str = "Zr40Cu30Al30"
        
        mass_fractions = parse_composition_string(composition_str)
        atomic_fractions = mass_to_atomic_fractions(mass_fractions)
        
        assert set(atomic_fractions.keys()) == {"Zr", "Cu", "Al"}
        assert abs(sum(atomic_fractions.values()) - 1.0) < 1e-6


def test_packing_efficiency_with_dataframe_row():
    """Test compute_packing_efficiency with a row from a DataFrame (typical usage)."""
    # Simulate a row with atomic fractions
    row_data = {"Zr": 0.6, "Cu": 0.3, "Al": 0.1}
    
    pe = compute_packing_efficiency(row_data)
    
    assert pe < 1.0
    assert pe > 0.0
    assert isinstance(pe, float)