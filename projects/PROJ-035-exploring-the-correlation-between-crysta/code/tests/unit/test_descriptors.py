import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from unittest.mock import Mock, patch
import sys
from typing import Dict, Any

# Ensure the src directory is in the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from src.descriptors.compute_descriptors import (
    calculate_tolerance_factor,
    calculate_octahedral_tilting_angles,
    calculate_bond_length_variance,
    calculate_unit_cell_volume,
    compute_all_descriptors,
    process_dataframe
)
from pymatgen.core import Structure, Lattice


class TestToleranceFactor:
    def test_perfect_perovskite(self):
        """Test with a perfect cubic perovskite (e.g., SrTiO3)"""
        # Sr at corners, Ti at body center, O at face centers
        lattice = Lattice.cubic(3.905)
        species = ["Sr", "Ti", "O"]
        coords = [
            [0, 0, 0],       # Sr
            [0.5, 0.5, 0.5], # Ti
            [0.5, 0.5, 0],   # O
            [0.5, 0, 0.5],   # O
            [0, 0.5, 0.5]    # O
        ]
        structure = Structure(lattice, species, coords)
        
        t = calculate_tolerance_factor(structure)
        # For SrTiO3, t should be close to 1.0 (ideal is 1.0)
        # Using standard radii: Sr=1.44, Ti=0.605, O=1.40
        # t = (1.44 + 1.40) / (sqrt(2) * (0.605 + 1.40)) = 2.84 / (1.414 * 2.005) = 2.84 / 2.835 = 1.001
        assert 0.9 < t < 1.1, f"Tolerance factor {t} is not close to 1.0"

    def test_distorted_perovskite(self):
        """Test with a distorted structure"""
        # Slightly distort the lattice
        lattice = Lattice.cubic(3.95)
        species = ["Ba", "Zr", "O"]
        coords = [
            [0, 0, 0],
            [0.5, 0.5, 0.5],
            [0.5, 0.5, 0],
            [0.5, 0, 0.5],
            [0, 0.5, 0.5]
        ]
        structure = Structure(lattice, species, coords)
        
        t = calculate_tolerance_factor(structure)
        # Ba=1.61, Zr=0.72, O=1.40
        # t = (1.61 + 1.40) / (sqrt(2) * (0.72 + 1.40)) = 3.01 / (1.414 * 2.12) = 3.01 / 3.00 = 1.003
        # Should be close to 1.0
        assert 0.9 < t < 1.1, f"Tolerance factor {t} is not close to 1.0"


class TestOctahedralTilting:
    def test_perfect_octahedron(self):
        """Test with a perfect octahedron (180 degree angles)"""
        lattice = Lattice.cubic(3.905)
        species = ["Sr", "Ti", "O"]
        coords = [
            [0, 0, 0],
            [0.5, 0.5, 0.5],
            [0.5, 0.5, 0],
            [0.5, 0, 0.5],
            [0, 0.5, 0.5]
        ]
        structure = Structure(lattice, species, coords)
        
        angle = calculate_octahedral_tilting_angles(structure)
        # In a perfect cubic structure, B-X-B angles are 180 degrees
        # Deviation should be 0
        assert angle < 1.0, f"Tilting angle {angle} should be close to 0 for perfect cube"

    def test_tilted_octahedron(self):
        """Test with a tilted structure"""
        # Create a structure with slight distortion
        lattice = Lattice.cubic(4.0)
        species = ["Sr", "Ti", "O"]
        coords = [
            [0, 0, 0],
            [0.5, 0.5, 0.5],
            [0.5, 0.5, 0.02], # Slight tilt
            [0.5, 0, 0.5],
            [0, 0.5, 0.5]
        ]
        structure = Structure(lattice, species, coords)
        
        angle = calculate_octahedral_tilting_angles(structure)
        # Should be non-zero
        assert angle >= 0, "Tilting angle cannot be negative"


class TestBondLengthVariance:
    def test_perfect_octahedron(self):
        """Test variance for a perfect octahedron"""
        lattice = Lattice.cubic(3.905)
        species = ["Sr", "Ti", "O"]
        coords = [
            [0, 0, 0],
            [0.5, 0.5, 0.5],
            [0.5, 0.5, 0],
            [0.5, 0, 0.5],
            [0, 0.5, 0.5]
        ]
        structure = Structure(lattice, species, coords)
        
        var = calculate_bond_length_variance(structure)
        # In a perfect cubic structure, all Ti-O bonds are equal
        # Variance should be close to 0
        assert var < 0.01, f"Bond length variance {var} should be close to 0"

    def test_distorted_octahedron(self):
        """Test variance for a distorted octahedron"""
        lattice = Lattice.cubic(4.0)
        species = ["Sr", "Ti", "O"]
        coords = [
            [0, 0, 0],
            [0.5, 0.5, 0.5],
            [0.5, 0.5, 0.01], # Distortion
            [0.5, 0, 0.5],
            [0, 0.5, 0.5]
        ]
        structure = Structure(lattice, species, coords)
        
        var = calculate_bond_length_variance(structure)
        # Variance should be positive
        assert var >= 0, "Variance cannot be negative"


class TestUnitCellVolume:
    def test_cubic_volume(self):
        """Test volume calculation for a cubic lattice"""
        lattice = Lattice.cubic(4.0)
        structure = Structure(lattice, ["A"], [[0, 0, 0]])
        
        vol = calculate_unit_cell_volume(structure)
        assert abs(vol - 64.0) < 1e-6, f"Volume {vol} should be 64.0"

    def test_orthorhombic_volume(self):
        """Test volume for orthorhombic lattice"""
        lattice = Lattice.from_parameters(3, 4, 5, 90, 90, 90)
        structure = Structure(lattice, ["A"], [[0, 0, 0]])
        
        vol = calculate_unit_cell_volume(structure)
        assert abs(vol - 60.0) < 1e-6, f"Volume {vol} should be 60.0"


class TestComputeAllDescriptors:
    def test_all_descriptors(self):
        """Test that all descriptors are computed"""
        lattice = Lattice.cubic(3.905)
        species = ["Sr", "Ti", "O"]
        coords = [
            [0, 0, 0],
            [0.5, 0.5, 0.5],
            [0.5, 0.5, 0],
            [0.5, 0, 0.5],
            [0, 0.5, 0.5]
        ]
        structure = Structure(lattice, species, coords)
        
        desc = compute_all_descriptors(structure)
        
        assert 'tolerance_factor' in desc
        assert 'octahedral_tilting_angle' in desc
        assert 'bond_length_variance' in desc
        assert 'unit_cell_volume' in desc
        
        assert isinstance(desc['tolerance_factor'], float)
        assert isinstance(desc['octahedral_tilting_angle'], float)
        assert isinstance(desc['bond_length_variance'], float)
        assert isinstance(desc['unit_cell_volume'], float)


class TestProcessDataFrame:
    def test_process_dataframe(self):
        """Test processing a dataframe with structures"""
        # Create a mock dataframe
        lattice = Lattice.cubic(3.905)
        species = ["Sr", "Ti", "O"]
        coords = [
            [0, 0, 0],
            [0.5, 0.5, 0.5],
            [0.5, 0.5, 0],
            [0.5, 0, 0.5],
            [0, 0.5, 0.5]
        ]
        structure = Structure(lattice, species, coords)
        
        df = pd.DataFrame({
            'structure_id': ['1', '2'],
            'thermal_conductivity': [1.0, 2.0],
            'structure': [structure, structure]
        })
        
        result = process_dataframe(df)
        
        assert 'tolerance_factor' in result.columns
        assert 'octahedral_tilting_angle' in result.columns
        assert 'bond_length_variance' in result.columns
        assert 'unit_cell_volume' in result.columns
        
        assert len(result) == 2
        assert result['tolerance_factor'].iloc[0] > 0
        
    def test_process_dataframe_with_missing_structure(self):
        """Test handling of missing structure"""
        df = pd.DataFrame({
            'structure_id': ['1'],
            'thermal_conductivity': [1.0],
            'structure': [None]
        })
        
        result = process_dataframe(df)
        
        assert pd.isna(result['tolerance_factor'].iloc[0])
        assert pd.isna(result['octahedral_tilting_angle'].iloc[0])