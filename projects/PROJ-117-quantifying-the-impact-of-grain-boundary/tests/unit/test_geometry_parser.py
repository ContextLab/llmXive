"""
Unit tests for geometry_parser.py (T010)
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import os

from code.geometry_parser import (
    calculate_sigma_value,
    calculate_miller_indices,
    calculate_rodrigues_vector,
    extract_boundary_plane_normal,
    calculate_boundary_width,
    calculate_excess_volume,
    parse_structure_file,
    process_raw_data
)
from pymatgen.core import Structure, Lattice

class TestCalculateSigmaValue:
    def test_sigma3(self):
        """Test Σ3 calculation for 60° misorientation"""
        sigma = calculate_sigma_value(60.0)
        assert sigma == 3

    def test_sigma5(self):
        """Test Σ5 calculation for 36.87° misorientation"""
        sigma = calculate_sigma_value(36.87)
        assert sigma == 5

    def test_sigma9(self):
        """Test Σ9 calculation for 38.94° misorientation"""
        sigma = calculate_sigma_value(38.94)
        assert sigma == 9

    def test_random_boundary(self):
        """Test that non-special angles return Σ=1"""
        sigma = calculate_sigma_value(45.0)
        assert sigma == 1

    def test_angle_normalization(self):
        """Test that angles > 90° are normalized"""
        sigma1 = calculate_sigma_value(120.0)  # Should be equivalent to 60°
        sigma2 = calculate_sigma_value(60.0)
        assert sigma1 == sigma2

class TestCalculateMillerIndices:
    def test_simple_miller_indices(self):
        """Test Miller indices calculation for simple cases"""
        # Create a simple cubic lattice
        lattice = Lattice.cubic(4.0)
        
        # Test [001] direction
        normal = np.array([0.0, 0.0, 1.0])
        miller = calculate_miller_indices(normal, lattice)
        assert miller == (0, 0, 1) or miller == (0, 0, -1)

    def test_non_trivial_miller_indices(self):
        """Test Miller indices for non-trivial directions"""
        lattice = Lattice.cubic(4.0)
        
        # Test [111] direction
        normal = np.array([1.0, 1.0, 1.0]) / np.sqrt(3.0)
        miller = calculate_miller_indices(normal, lattice)
        # Should be close to (1, 1, 1)
        assert sum(abs(np.array(miller) - np.array([1, 1, 1]))) < 1.0

class TestCalculateRodriguesVector:
    def test_zero_rotation(self):
        """Test Rodrigues vector for zero rotation"""
        rotation_matrix = np.eye(3)
        rodrigues = calculate_rodrigues_vector(rotation_matrix)
        assert np.allclose(rodrigues, [0.0, 0.0, 0.0])

    def test_180_degree_rotation(self):
        """Test Rodrigues vector for 180° rotation"""
        # 180° rotation around z-axis
        rotation_matrix = np.array([
            [-1, 0, 0],
            [0, -1, 0],
            [0, 0, 1]
        ])
        rodrigues = calculate_rodrigues_vector(rotation_matrix)
        # For 180°, tan(90°) is infinite, but our implementation should handle it
        assert len(rodrigues) == 3

class TestExtractBoundaryPlaneNormal:
    def test_default_normal(self):
        """Test that the default boundary plane normal is along z-axis"""
        lattice = Lattice.cubic(4.0)
        structure = Structure(lattice, ['Fe'], [[0, 0, 0]])
        
        normal, miller = extract_boundary_plane_normal(structure)
        assert np.allclose(normal, [0.0, 0.0, 1.0])
        assert miller == (0, 0, 1) or miller == (0, 0, -1)

class TestCalculateBoundaryWidth:
    def test_boundary_width(self):
        """Test boundary width calculation"""
        lattice = Lattice.cubic(4.0)
        structure = Structure(lattice, ['Fe'], [[0, 0, 0]])
        
        width = calculate_boundary_width(structure)
        assert width == 4.0

class TestCalculateExcessVolume:
    def test_excess_volume(self):
        """Test excess volume calculation"""
        lattice = Lattice.cubic(4.0)
        structure = Structure(lattice, ['Fe'], [[0, 0, 0]])
        
        excess_volume = calculate_excess_volume(structure)
        # The exact value depends on the implementation, but it should be a float
        assert isinstance(excess_volume, float)

class TestParseStructureFile:
    @pytest.fixture
    def temp_poscar(self):
        """Create a temporary POSCAR file for testing"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.vasp', delete=False) as f:
            f.write("""Test structure
            1.0
            4.0 0.0 0.0
            0.0 4.0 0.0
            0.0 0.0 4.0
            Fe
            1
            Direct
            0.0 0.0 0.0
            """)
            temp_path = f.name
        yield temp_path
        os.unlink(temp_path)

    def test_parse_poscar(self, temp_poscar):
        """Test parsing a POSCAR file"""
        result = parse_structure_file(temp_poscar)
        
        assert 'file_path' in result
        assert 'num_atoms' in result
        assert result['num_atoms'] == 1
        assert 'lattice_params' in result
        assert 'boundary_plane_miller_indices' in result

class TestProcessRawData:
    @pytest.fixture
    def temp_metadata(self):
        """Create a temporary metadata file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            import json
            json.dump({
                'files': [
                    {
                        'file_name': 'test.vasp',
                        'misorientation_angle': 60.0,
                        'material_id': 'mp-123',
                        'source': 'test',
                        'checksum': 'abc123'
                    }
                ]
            }, f)
            temp_path = f.name
        yield temp_path
        os.unlink(temp_path)

    @pytest.fixture
    def temp_raw_dir(self, temp_poscar):
        """Create a temporary raw data directory"""
        temp_dir = tempfile.mkdtemp()
        # Copy the temp_poscar to the temp directory
        import shutil
        shutil.copy(temp_poscar, os.path.join(temp_dir, 'test.vasp'))
        yield temp_dir
        import shutil
        shutil.rmtree(temp_dir)

    def test_process_raw_data(self, temp_metadata, temp_raw_dir, temp_poscar):
        """Test processing raw data"""
        df = process_raw_data(temp_raw_dir, temp_metadata)
        
        assert not df.empty
        assert 'file_name' in df.columns
        assert 'sigma_value' in df.columns
        assert 'misorientation_angle' in df.columns

if __name__ == '__main__':
    pytest.main([__file__, '-v'])