"""
Unit tests for descriptor calculation (δ, ΔHmix, VEC, Δχ) in code/data/features.py.

These tests verify the mathematical correctness of the feature engineering pipeline
by comparing calculated values against hand-computed reference values for known
compositions.
"""
import unittest
import math
import sys
import os
from pathlib import Path
from typing import Dict, List, Any

# Add project root to path to allow imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

# Import the function to test
from code.data.features import calculate_delta, calculate_dh_mix, calculate_VEC, calculate_delta_chi


class TestDescriptorCalculations(unittest.TestCase):
    """Test cases for BMG descriptor calculations."""

    def test_calculate_delta(self):
        """Test atomic radius mismatch (δ) calculation.
        
        Formula: δ = sqrt(Σ c_i (1 - r_i / r_avg)^2) * 100
        
        Reference: For a binary alloy A (c=0.5, r=1.0) and B (c=0.5, r=2.0):
        r_avg = 0.5*1.0 + 0.5*2.0 = 1.5
        term_A = 0.5 * (1 - 1.0/1.5)^2 = 0.5 * (0.333)^2 = 0.0555
        term_B = 0.5 * (1 - 2.0/1.5)^2 = 0.5 * (-0.333)^2 = 0.0555
        δ = sqrt(0.0555 + 0.0555) * 100 = sqrt(0.111) * 100 ≈ 33.33
        """
        composition = [
            {"element": "A", "at_frac": 0.5, "radius": 1.0},
            {"element": "B", "at_frac": 0.5, "radius": 2.0},
        ]
        
        result = calculate_delta(composition)
        expected = math.sqrt(0.5 * (1 - 1.0/1.5)**2 + 0.5 * (1 - 2.0/1.5)**2) * 100
        
        self.assertAlmostEqual(result, expected, places=5, 
                             msg=f"δ calculation mismatch: got {result}, expected {expected}")

    def test_calculate_dh_mix(self):
        """Test mixing enthalpy (ΔHmix) calculation.
        
        Formula: ΔHmix = 4 * Σ Σ c_i c_j ΔH_ij (for i != j)
        
        Reference: Binary A-B with c_A=0.5, c_B=0.5, ΔH_AB = -10 kJ/mol
        ΔHmix = 4 * (0.5 * 0.5 * (-10)) = 4 * (-2.5) = -10.0 kJ/mol
        """
        # Mock interaction enthalpy matrix
        # In real code, this comes from Miedema or similar
        interaction_matrix = {
            ("A", "B"): -10.0,
            ("B", "A"): -10.0,
            ("A", "A"): 0.0,
            ("B", "B"): 0.0,
        }
        
        composition = [
            {"element": "A", "at_frac": 0.5},
            {"element": "B", "at_frac": 0.5},
        ]
        
        result = calculate_dh_mix(composition, interaction_matrix)
        expected = 4 * (0.5 * 0.5 * -10.0)  # = -10.0
        
        self.assertAlmostEqual(result, expected, places=5,
                             msg=f"ΔHmix calculation mismatch: got {result}, expected {expected}")

    def test_calculate_VEC(self):
        """Test Valence Electron Concentration (VEC) calculation.
        
        Formula: VEC = Σ c_i * VEC_i
        
        Reference: Binary A (c=0.5, VEC=1) and B (c=0.5, VEC=3)
        VEC = 0.5*1 + 0.5*3 = 2.0
        """
        composition = [
            {"element": "A", "at_frac": 0.5, "valence": 1},
            {"element": "B", "at_frac": 0.5, "valence": 3},
        ]
        
        result = calculate_VEC(composition)
        expected = 0.5 * 1 + 0.5 * 3
        
        self.assertAlmostEqual(result, expected, places=5,
                             msg=f"VEC calculation mismatch: got {result}, expected {expected}")

    def test_calculate_delta_chi(self):
        """Test electronegativity difference (Δχ) calculation.
        
        Formula: Δχ = sqrt(Σ c_i (χ_i - χ_avg)^2)
        
        Reference: Binary A (c=0.5, χ=1.0) and B (c=0.5, χ=2.0)
        χ_avg = 0.5*1.0 + 0.5*2.0 = 1.5
        term_A = 0.5 * (1.0 - 1.5)^2 = 0.5 * 0.25 = 0.125
        term_B = 0.5 * (2.0 - 1.5)^2 = 0.5 * 0.25 = 0.125
        Δχ = sqrt(0.125 + 0.125) = sqrt(0.25) = 0.5
        """
        composition = [
            {"element": "A", "at_frac": 0.5, "electronegativity": 1.0},
            {"element": "B", "at_frac": 0.5, "electronegativity": 2.0},
        ]
        
        result = calculate_delta_chi(composition)
        expected = math.sqrt(0.5 * (1.0 - 1.5)**2 + 0.5 * (2.0 - 1.5)**2)
        
        self.assertAlmostEqual(result, expected, places=5,
                             msg=f"Δχ calculation mismatch: got {result}, expected {expected}")

    def test_calculate_delta_single_element(self):
        """Test that single element alloy has δ = 0."""
        composition = [
            {"element": "Fe", "at_frac": 1.0, "radius": 1.24},
        ]
        
        result = calculate_delta(composition)
        self.assertAlmostEqual(result, 0.0, places=5,
                             msg="Single element alloy should have δ = 0")

    def test_calculate_VEC_single_element(self):
        """Test VEC for single element."""
        composition = [
            {"element": "Cu", "at_frac": 1.0, "valence": 1},
        ]
        
        result = calculate_VEC(composition)
        self.assertAlmostEqual(result, 1.0, places=5,
                             msg="VEC should equal valence for single element")

    def test_empty_composition_raises(self):
        """Test that empty composition raises an error."""
        with self.assertRaises(ValueError):
            calculate_delta([])
        
        with self.assertRaises(ValueError):
            calculate_VEC([])
        
        with self.assertRaises(ValueError):
            calculate_delta_chi([])

    def test_composition_sum_not_one(self):
        """Test behavior when composition doesn't sum to 1.
        
        The function should normalize or handle this gracefully.
        We test that it doesn't crash and produces a reasonable result.
        """
        composition = [
            {"element": "A", "at_frac": 0.6, "radius": 1.0},
            {"element": "B", "at_frac": 0.6, "radius": 2.0},
        ]
        
        # Should not raise, but produce a result
        result = calculate_delta(composition)
        self.assertIsInstance(result, float)


if __name__ == "__main__":
    unittest.main()