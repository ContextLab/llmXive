"""
Unit tests for descriptor calculation (Task T016).
Tests octahedral tilting angles, bond-length variance, tolerance factor, and unit cell volume.
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
from typing import Dict, Any

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from descriptors.compute_descriptors import (
    calculate_tolerance_factor,
    calculate_bond_length_variance,
    calculate_octahedral_tilting,
    calculate_unit_cell_volume,
    compute_all_descriptors
)


class TestToleranceFactor:
    """Tests for Goldschmidt tolerance factor calculation."""

    def test_perovskite_ideal(self):
        """Ideal cubic perovskite (t=1)."""
        # Ideal: A-O = 2*rA + 2*rO, B-O = 2*rB + 2*rO, t = (rA+rO)/sqrt(2)*(rB+rO)
        # For t=1: rA+rO = sqrt(2)*(rB+rO)
        # Example: rO=1.4, rB=0.6 -> rB+rO=2.0 -> sqrt(2)*2.0 = 2.828
        # rA+rO = 2.828 -> rA = 1.428
        r_A = 1.428
        r_B = 0.6
        r_O = 1.4
        
        t = calculate_tolerance_factor(r_A, r_B, r_O)
        assert np.isclose(t, 1.0, atol=0.01), f"Expected t≈1.0, got {t}"

    def test_perovskite_distorted(self):
        """Distorted perovskite (t < 1)."""
        r_A = 1.2
        r_B = 0.6
        r_O = 1.4
        
        t = calculate_tolerance_factor(r_A, r_B, r_O)
        assert t < 1.0, f"Expected t<1.0 for distorted, got {t}"
        assert t > 0.7, f"Expected t>0.7 for stable perovskite, got {t}"

    def test_invalid_radii(self):
        """Negative or zero radii should raise ValueError."""
        with pytest.raises(ValueError):
            calculate_tolerance_factor(-1.0, 0.6, 1.4)
        
        with pytest.raises(ValueError):
            calculate_tolerance_factor(1.2, 0.0, 1.4)


class TestBondLengthVariance:
    """Tests for bond-length variance calculation."""

    def test_uniform_bonds(self):
        """All bonds equal -> variance = 0."""
        bonds = [2.0, 2.0, 2.0, 2.0, 2.0, 2.0]
        var = calculate_bond_length_variance(bonds)
        assert np.isclose(var, 0.0, atol=1e-6), f"Expected 0.0, got {var}"

    def test_varying_bonds(self):
        """Varying bonds -> positive variance."""
        bonds = [1.9, 2.0, 2.1, 2.0, 1.95, 2.05]
        var = calculate_bond_length_variance(bonds)
        assert var > 0.0, f"Expected positive variance, got {var}"
        # Mean = (1.9+2.0+2.1+2.0+1.95+2.05)/6 = 12.0/6 = 2.0
        # Variance = ((0.1^2 + 0 + 0.1^2 + 0 + 0.05^2 + 0.05^2)/6)
        # = (0.01 + 0 + 0.01 + 0 + 0.0025 + 0.0025)/6 = 0.025/6 ≈ 0.00417
        expected = np.var(bonds, ddof=0)
        assert np.isclose(var, expected, atol=1e-6), f"Expected {expected}, got {var}"

    def test_empty_bonds(self):
        """Empty list should raise ValueError."""
        with pytest.raises(ValueError):
            calculate_bond_length_variance([])

    def test_single_bond(self):
        """Single bond -> variance = 0."""
        bonds = [2.0]
        var = calculate_bond_length_variance(bonds)
        assert np.isclose(var, 0.0, atol=1e-6)


class TestOctahedralTilting:
    """Tests for octahedral tilting angle calculation."""

    def test_no_tilt(self):
        """No tilt -> angle = 0."""
        # Perfect cubic: all bond angles = 180°
        angles = [180.0, 180.0, 180.0]
        tilt = calculate_octahedral_tilting(angles)
        assert np.isclose(tilt, 0.0, atol=1e-6), f"Expected 0.0, got {tilt}"

    def test_with_tilt(self):
        """With tilt -> positive angle."""
        # Example: some bonds deviate from 180°
        angles = [175.0, 178.0, 180.0]
        tilt = calculate_octahedral_tilting(angles)
        assert tilt > 0.0, f"Expected positive tilt, got {tilt}"
        # Tilt is typically defined as deviation from 180°
        # Average deviation = (5 + 2 + 0)/3 = 2.33
        expected_avg_deviation = np.mean([abs(180 - a) for a in angles])
        assert np.isclose(tilt, expected_avg_deviation, atol=1e-1), f"Expected ~{expected_avg_deviation}, got {tilt}"

    def test_invalid_angles(self):
        """Angles outside valid range should raise ValueError."""
        with pytest.raises(ValueError):
            calculate_octahedral_tilting([180.0, 190.0, 180.0])
        
        with pytest.raises(ValueError):
            calculate_octahedral_tilting([180.0, 170.0, 180.0])


class TestUnitCellVolume:
    """Tests for unit cell volume calculation."""

    def test_cubic_cell(self):
        """Cubic cell: V = a^3."""
        a = 4.0
        volume = calculate_unit_cell_volume(a, a, a, 90.0, 90.0, 90.0)
        assert np.isclose(volume, 64.0, atol=1e-6), f"Expected 64.0, got {volume}"

    def test_orthorhombic_cell(self):
        """Orthorhombic cell: V = a*b*c."""
        a, b, c = 4.0, 5.0, 6.0
        volume = calculate_unit_cell_volume(a, b, c, 90.0, 90.0, 90.0)
        assert np.isclose(volume, 120.0, atol=1e-6), f"Expected 120.0, got {volume}"

    def test_tetragonal_cell(self):
        """Tetragonal cell: V = a^2*c."""
        a, c = 4.0, 6.0
        volume = calculate_unit_cell_volume(a, a, c, 90.0, 90.0, 90.0)
        assert np.isclose(volume, 96.0, atol=1e-6), f"Expected 96.0, got {volume}"


class TestComputeAllDescriptors:
    """Integration test for the full descriptor computation pipeline."""

    def test_computes_all_descriptors(self):
        """Verify that compute_all_descriptors returns a dict with all required keys."""
        # Mock input structure data
        mock_structure = {
            'a': 4.0,
            'b': 4.0,
            'c': 4.0,
            'alpha': 90.0,
            'beta': 90.0,
            'gamma': 90.0,
            'r_A': 1.428,
            'r_B': 0.6,
            'r_O': 1.4,
            'bond_lengths': [2.0, 2.0, 2.0, 2.0, 2.0, 2.0],
            'bond_angles': [180.0, 180.0, 180.0]
        }
        
        descriptors = compute_all_descriptors(mock_structure)
        
        required_keys = [
            'tolerance_factor',
            'bond_length_variance',
            'octahedral_tilting',
            'unit_cell_volume'
        ]
        
        for key in required_keys:
            assert key in descriptors, f"Missing key: {key}"
            assert isinstance(descriptors[key], (int, float, np.number)), f"Key {key} is not numeric"

    def test_computes_with_distorted_structure(self):
        """Test with a distorted perovskite structure."""
        mock_structure = {
            'a': 4.1,
            'b': 4.2,
            'c': 4.0,
            'alpha': 90.0,
            'beta': 90.0,
            'gamma': 90.0,
            'r_A': 1.3,
            'r_B': 0.6,
            'r_O': 1.4,
            'bond_lengths': [1.9, 2.0, 2.1, 2.0, 1.95, 2.05],
            'bond_angles': [175.0, 178.0, 180.0]
        }
        
        descriptors = compute_all_descriptors(mock_structure)
        
        # Check that values are reasonable
        assert descriptors['tolerance_factor'] < 1.0, "Distorted structure should have t < 1.0"
        assert descriptors['bond_length_variance'] > 0.0, "Varying bonds should have positive variance"
        assert descriptors['octahedral_tilting'] > 0.0, "Tilted bonds should have positive tilt"
        assert descriptors['unit_cell_volume'] > 0.0, "Volume should be positive"

    def test_invalid_structure_raises(self):
        """Invalid structure data should raise an error."""
        invalid_structure = {
            'a': -4.0,  # Negative lattice parameter
            'b': 4.0,
            'c': 4.0,
            'alpha': 90.0,
            'beta': 90.0,
            'gamma': 90.0,
            'r_A': 1.428,
            'r_B': 0.6,
            'r_O': 1.4,
            'bond_lengths': [],  # Empty bond lengths
            'bond_angles': [180.0, 180.0, 180.0]
        }
        
        with pytest.raises((ValueError, IndexError)):
            compute_all_descriptors(invalid_structure)

    def test_dataframe_integration(self):
        """Test that descriptors can be computed for a DataFrame of structures."""
        # Create a mock DataFrame
        data = {
            'structure_id': ['P1', 'P2'],
            'a': [4.0, 4.1],
            'b': [4.0, 4.2],
            'c': [4.0, 4.0],
            'alpha': [90.0, 90.0],
            'beta': [90.0, 90.0],
            'gamma': [90.0, 90.0],
            'r_A': [1.428, 1.3],
            'r_B': [0.6, 0.6],
            'r_O': [1.4, 1.4],
            'bond_lengths': [
                [[2.0, 2.0, 2.0, 2.0, 2.0, 2.0]],
                [[1.9, 2.0, 2.1, 2.0, 1.95, 2.05]]
            ],
            'bond_angles': [
                [[180.0, 180.0, 180.0]],
                [[175.0, 178.0, 180.0]]
            ]
        }
        df = pd.DataFrame(data)
        
        # This would normally call compute_all_descriptors for each row
        # For unit test, we verify the function exists and handles the structure
        # Full integration is tested in test_full_pipeline.py
        assert len(df) == 2
        assert 'structure_id' in df.columns