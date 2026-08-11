"""
Unit tests for descriptor calculation module.

Tests for compute_descriptors.py (T018)
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from unittest.mock import Mock, patch
import sys

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from pymatgen.core import Structure, Lattice, Species
from src.descriptors.compute_descriptors import (
    calculate_tolerance_factor,
    calculate_octahedral_tilting_angles,
    calculate_bond_length_variance,
    calculate_unit_cell_volume,
    compute_all_descriptors,
    process_dataframe
)


class TestToleranceFactor:
    """Tests for tolerance factor calculation."""

    def test_perovskite_tolerance_factor(self):
        """Test tolerance factor calculation for a standard perovskite."""
        # Create a simple cubic perovskite structure (e.g., SrTiO3)
        # Lattice parameter ~3.9 Angstroms
        lattice = Lattice.cubic(3.9)
        species = ['Sr', 'Ti', 'O', 'O', 'O']
        coords = [
            [0, 0, 0],       # Sr at corner (A-site)
            [0.5, 0.5, 0.5], # Ti at body center (B-site)
            [0.5, 0.5, 0],   # O at face centers (X-site)
            [0.5, 0, 0.5],
            [0, 0.5, 0.5]
        ]
        
        structure = Structure(lattice, species, coords)
        
        t = calculate_tolerance_factor(structure)
        
        # For SrTiO3, t should be close to 1.0 (ideal perovskite)
        # Typical range: 0.8 - 1.1
        assert not np.isnan(t), "Tolerance factor should not be NaN"
        assert 0.5 < t < 1.5, f"Tolerance factor {t} out of expected range"

    def test_invalid_structure(self):
        """Test tolerance factor with invalid structure."""
        # Create a non-perovskite structure
        lattice = Lattice.cubic(5.0)
        species = ['Fe', 'O']
        coords = [[0, 0, 0], [0.5, 0.5, 0.5]]
        
        structure = Structure(lattice, species, coords)
        
        t = calculate_tolerance_factor(structure)
        # Should return NaN or handle gracefully
        assert isinstance(t, float), "Should return a float"


class TestOctahedralTilting:
    """Tests for octahedral tilting angle calculation."""

    def test_ideal_perovskite_tilting(self):
        """Test tilting angles for an ideal (untilted) perovskite."""
        lattice = Lattice.cubic(3.9)
        species = ['Sr', 'Ti', 'O', 'O', 'O']
        coords = [
            [0, 0, 0],
            [0.5, 0.5, 0.5],
            [0.5, 0.5, 0],
            [0.5, 0, 0.5],
            [0, 0.5, 0.5]
        ]
        
        structure = Structure(lattice, species, coords)
        
        tilting = calculate_octahedral_tilting_angles(structure)
        
        assert 'mean_angle' in tilting
        assert 'std_angle' in tilting
        assert not np.isnan(tilting['mean_angle']), "Mean angle should not be NaN"

    def test_tilted_perovskite(self):
        """Test tilting angles for a distorted perovskite."""
        # Create a slightly distorted structure
        lattice = Lattice([[3.9, 0, 0], [0, 3.9, 0], [0, 0, 4.0]])  # Slightly stretched
        species = ['Sr', 'Ti', 'O', 'O', 'O']
        coords = [
            [0, 0, 0],
            [0.5, 0.5, 0.5],
            [0.5, 0.5, 0],
            [0.5, 0, 0.5],
            [0, 0.5, 0.5]
        ]
        
        structure = Structure(lattice, species, coords)
        
        tilting = calculate_octahedral_tilting_angles(structure)
        
        assert not np.isnan(tilting['mean_angle'])
        assert tilting['min_angle'] <= tilting['mean_angle'] <= tilting['max_angle']


class TestBondLengthVariance:
    """Tests for bond length variance calculation."""

    def test_ideal_bond_lengths(self):
        """Test bond length variance for an ideal perovskite."""
        lattice = Lattice.cubic(3.9)
        species = ['Sr', 'Ti', 'O', 'O', 'O']
        coords = [
            [0, 0, 0],
            [0.5, 0.5, 0.5],
            [0.5, 0.5, 0],
            [0.5, 0, 0.5],
            [0, 0.5, 0.5]
        ]
        
        structure = Structure(lattice, species, coords)
        
        bond_var = calculate_bond_length_variance(structure)
        
        assert 'mean_length' in bond_var
        assert 'variance' in bond_var
        assert not np.isnan(bond_var['mean_length'])
        assert bond_var['variance'] >= 0

    def test_distorted_bond_lengths(self):
        """Test bond length variance for a distorted perovskite."""
        lattice = Lattice([[3.8, 0, 0], [0, 3.9, 0], [0, 0, 4.1]])
        species = ['Sr', 'Ti', 'O', 'O', 'O']
        coords = [
            [0, 0, 0],
            [0.5, 0.5, 0.5],
            [0.5, 0.5, 0],
            [0.5, 0, 0.5],
            [0, 0.5, 0.5]
        ]
        
        structure = Structure(lattice, species, coords)
        
        bond_var = calculate_bond_length_variance(structure)
        
        assert not np.isnan(bond_var['mean_length'])
        assert bond_var['min_length'] <= bond_var['mean_length'] <= bond_var['max_length']


class TestUnitCellVolume:
    """Tests for unit cell volume calculation."""

    def test_cubic_volume(self):
        """Test volume calculation for cubic lattice."""
        lattice = Lattice.cubic(4.0)
        species = ['Sr', 'Ti', 'O']
        coords = [[0, 0, 0], [0.5, 0.5, 0.5], [0.5, 0.5, 0]]
        
        structure = Structure(lattice, species, coords)
        
        volume = calculate_unit_cell_volume(structure)
        
        assert volume == pytest.approx(64.0, rel=1e-5)  # 4^3 = 64

    def test_tetragonal_volume(self):
        """Test volume calculation for tetragonal lattice."""
        lattice = Lattice([[4.0, 0, 0], [0, 4.0, 0], [0, 0, 5.0]])
        species = ['Sr', 'Ti', 'O']
        coords = [[0, 0, 0], [0.5, 0.5, 0.5], [0.5, 0.5, 0]]
        
        structure = Structure(lattice, species, coords)
        
        volume = calculate_unit_cell_volume(structure)
        
        assert volume == pytest.approx(80.0, rel=1e-5)  # 4 * 4 * 5 = 80


class TestComputeAllDescriptors:
    """Tests for the combined descriptor computation."""

    def test_all_descriptors_computed(self):
        """Test that all descriptors are computed for a structure."""
        lattice = Lattice.cubic(3.9)
        species = ['Sr', 'Ti', 'O', 'O', 'O']
        coords = [
            [0, 0, 0],
            [0.5, 0.5, 0.5],
            [0.5, 0.5, 0],
            [0.5, 0, 0.5],
            [0, 0.5, 0.5]
        ]
        
        structure = Structure(lattice, species, coords)
        
        descriptors = compute_all_descriptors(structure)
        
        # Check all expected keys exist
        expected_keys = [
            'tolerance_factor',
            'tilting_mean_angle', 'tilting_std_angle', 
            'tilting_min_angle', 'tilting_max_angle',
            'bond_length_mean', 'bond_length_std',
            'bond_length_variance', 'bond_length_min', 'bond_length_max',
            'unit_cell_volume'
        ]
        
        for key in expected_keys:
            assert key in descriptors, f"Missing key: {key}"
            assert isinstance(descriptors[key], float), f"Key {key} should be float"


class TestProcessDataFrame:
    """Tests for DataFrame processing."""

    def test_process_single_structure(self):
        """Test processing a DataFrame with one structure."""
        # Create a mock structure
        lattice = Lattice.cubic(3.9)
        species = ['Sr', 'Ti', 'O', 'O', 'O']
        coords = [
            [0, 0, 0],
            [0.5, 0.5, 0.5],
            [0.5, 0.5, 0],
            [0.5, 0, 0.5],
            [0, 0.5, 0.5]
        ]
        structure = Structure(lattice, species, coords)
        
        df = pd.DataFrame({
            'id': [1],
            'structure': [structure]
        })
        
        result = process_dataframe(df, structure_column='structure')
        
        assert len(result) == 1
        assert 'tolerance_factor' in result.columns
        assert 'unit_cell_volume' in result.columns

    def test_process_multiple_structures(self):
        """Test processing a DataFrame with multiple structures."""
        structures = []
        for i, a in enumerate([3.9, 4.0, 4.1]):
            lattice = Lattice.cubic(a)
            species = ['Sr', 'Ti', 'O', 'O', 'O']
            coords = [
                [0, 0, 0],
                [0.5, 0.5, 0.5],
                [0.5, 0.5, 0],
                [0.5, 0, 0.5],
                [0, 0.5, 0.5]
            ]
            structures.append(Structure(lattice, species, coords))
        
        df = pd.DataFrame({
            'id': [1, 2, 3],
            'structure': structures
        })
        
        result = process_dataframe(df, structure_column='structure')
        
        assert len(result) == 3
        assert 'tolerance_factor' in result.columns
        assert all(result['tolerance_factor'].notna())

    def test_process_with_missing_structures(self):
        """Test processing when some structures are invalid."""
        lattice = Lattice.cubic(3.9)
        species = ['Sr', 'Ti', 'O', 'O', 'O']
        coords = [
            [0, 0, 0],
            [0.5, 0.5, 0.5],
            [0.5, 0.5, 0],
            [0.5, 0, 0.5],
            [0, 0.5, 0.5]
        ]
        valid_structure = Structure(lattice, species, coords)
        
        df = pd.DataFrame({
            'id': [1, 2, 3],
            'structure': [valid_structure, None, valid_structure]
        })
        
        result = process_dataframe(df, structure_column='structure')
        
        assert len(result) == 3
        # Should have NaN for the invalid entry
        assert result.loc[1, 'tolerance_factor'] != result.loc[1, 'tolerance_factor']  # NaN check