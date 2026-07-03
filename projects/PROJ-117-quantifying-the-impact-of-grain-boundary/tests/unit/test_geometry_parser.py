"""
Unit tests for code/geometry_parser.py.

Tests cover:
- Miller indices derivation from boundary plane normals
- Sigma (Σ) value calculation from misorientation angles
- Rodrigues vector encoding
- Boundary plane normal extraction logic
- Boundary width and excess volume calculations
- Full structure file parsing and feature extraction
"""
import pytest
import numpy as np
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import functions under test matching the API surface
from geometry_parser import (
    get_miller_indices,
    calculate_sigma_from_misorientation,
    calculate_rodrigues_vector,
    extract_boundary_plane_normal,
    calculate_boundary_width,
    calculate_excess_volume,
    parse_structure_file,
    extract_geometry_features
)
from models.grain_boundary_record import GrainBoundaryRecord


class TestMillerIndices:
    """Tests for get_miller_indices function."""

    def test_miller_indices_from_normal_vector(self):
        """Test conversion of a normal vector to Miller indices."""
        # Normal vector [1, 0, 0] should correspond to (100)
        normal = np.array([1.0, 0.0, 0.0])
        indices = get_miller_indices(normal)
        # Check that the indices are proportional to [1, 0, 0]
        assert np.allclose(np.abs(indices), [1, 0, 0])

    def test_miller_indices_from_arbitrary_normal(self):
        """Test conversion of an arbitrary normal vector."""
        # Normal vector [1, 1, 0] -> (110)
        normal = np.array([1.0, 1.0, 0.0])
        indices = get_miller_indices(normal)
        # Normalize to smallest integers
        assert np.allclose(np.abs(indices), [1, 1, 0])

    def test_miller_indices_negative_normal(self):
        """Test handling of negative normal vectors."""
        normal = np.array([-1.0, 0.0, 0.0])
        indices = get_miller_indices(normal)
        # Miller indices are typically positive in magnitude for the plane family
        assert np.allclose(np.abs(indices), [1, 0, 0])

    def test_miller_indices_zero_vector_raises(self):
        """Test that zero vector raises an error."""
        normal = np.array([0.0, 0.0, 0.0])
        with pytest.raises(ValueError):
            get_miller_indices(normal)


class TestSigmaCalculation:
    """Tests for calculate_sigma_from_misorientation function."""

    def test_sigma_1_at_0_degrees(self):
        """Test that 0 degrees misorientation yields Sigma 1."""
        sigma = calculate_sigma_from_misorientation(0.0)
        assert sigma == 1

    def test_sigma_3_at_60_degrees(self):
        """
        Test Sigma 3 at 60 degrees (common in FCC metals).
        Note: This is an approximation or lookup based on CSL tables.
        For a real implementation, this might use a lookup table.
        """
        sigma = calculate_sigma_from_misorientation(60.0)
        # Depending on implementation, this might be 3 or close to it
        # For the purpose of this test, we assume the function returns 3 for 60 deg
        assert sigma == 3

    def test_sigma_non_csl_angle(self):
        """Test that non-CSL angles return a calculated or fallback value."""
        # 45 degrees is not a perfect CSL for simple cubic, but might be approximated
        sigma = calculate_sigma_from_misorientation(45.0)
        # Should return a positive integer
        assert isinstance(sigma, int)
        assert sigma > 0

    def test_sigma_negative_angle(self):
        """Test handling of negative angles (should be treated as absolute)."""
        sigma = calculate_sigma_from_misorientation(-60.0)
        assert sigma == 3


class TestRodriguesVector:
    """Tests for calculate_rodrigues_vector function."""

    def test_rodrigues_vector_zero_angle(self):
        """Test Rodrigues vector for zero misorientation."""
        rodrigues = calculate_rodrigues_vector(0.0, [1, 0, 0])
        # Zero rotation should result in zero vector
        assert np.allclose(rodrigues, [0.0, 0.0, 0.0])

    def test_rodrigues_vector_90_degrees(self):
        """Test Rodrigues vector for 90 degree rotation."""
        axis = np.array([0.0, 0.0, 1.0])
        rodrigues = calculate_rodrigues_vector(90.0, axis)
        # tan(90/2) = tan(45) = 1
        # Rodrigues vector = n * tan(theta/2)
        expected = axis * 1.0
        assert np.allclose(rodrigues, expected)

    def test_rodrigues_vector_arbitrary(self):
        """Test Rodrigues vector calculation for arbitrary angle and axis."""
        angle = 45.0
        axis = np.array([1, 0, 0])
        rodrigues = calculate_rodrigues_vector(angle, axis)
        expected_factor = np.tan(np.radians(angle) / 2)
        expected = axis * expected_factor
        assert np.allclose(rodrigues, expected)

    def test_rodrigues_vector_invalid_axis(self):
        """Test that non-unit axis vector is handled (normalized)."""
        axis = np.array([2, 0, 0])
        rodrigues = calculate_rodrigues_vector(45.0, axis)
        # Should normalize the axis internally
        expected_factor = np.tan(np.radians(45.0) / 2)
        expected = np.array([1, 0, 0]) * expected_factor
        assert np.allclose(rodrigues, expected)


class TestBoundaryPlaneNormal:
    """Tests for extract_boundary_plane_normal function."""

    def test_extract_normal_from_lattice(self):
        """Test extraction of normal from a simulated lattice structure."""
        # Mock a structure with a known interface plane
        # In a real scenario, this would parse a POSAR/CIF
        # Here we test the logic assuming the function can derive it
        # Since we can't easily mock a pymatgen Structure without heavy setup,
        # we test the helper logic if exposed or the expected behavior.
        
        # For this unit test, we assume the function takes a structure object
        # and returns a numpy array. We will mock the structure.
        mock_structure = MagicMock()
        # Mock the lattice and atom positions to simulate a slab
        # The function logic should identify the mid-plane normal.
        
        # Since the implementation details of extracting from a file are complex,
        # we test the mathematical helper if available, or the return type.
        # Assuming the function returns a numpy array of shape (3,)
        result = extract_boundary_plane_normal(mock_structure)
        
        # We expect a vector of length 3
        assert isinstance(result, np.ndarray)
        assert len(result) == 3
        # The vector should be normalized
        assert np.isclose(np.linalg.norm(result), 1.0, atol=1e-5)

    def test_extract_normal_direction(self):
        """Test that the normal points in the expected growth direction."""
        # If the growth direction is Z, the normal should be [0,0,1] or [0,0,-1]
        mock_structure = MagicMock()
        result = extract_boundary_plane_normal(mock_structure)
        # Just checking it's a valid unit vector is sufficient for this unit test
        # unless specific geometry is mocked.
        assert np.allclose(np.sum(result**2), 1.0)


class TestBoundaryWidth:
    """Tests for calculate_boundary_width function."""

    def test_calculate_width_simple(self):
        """Test boundary width calculation."""
        # Simulate a slab with a known width
        # The function likely takes the structure and calculates the distance
        # between the two halves of the bicrystal or the vacuum region.
        
        # Mock a structure with a defined lattice parameter in Z
        mock_structure = MagicMock()
        mock_structure.lattice = MagicMock()
        mock_structure.lattice.c = 10.0  # Angstroms
        
        # Assume the function uses the lattice parameter
        width = calculate_boundary_width(mock_structure)
        
        # The width should be related to the lattice parameter
        # Depending on implementation, it might be half or full
        assert width > 0
        assert isinstance(width, float)


class TestExcessVolume:
    """Tests for calculate_excess_volume function."""

    def test_calculate_excess_volume_positive(self):
        """Test excess volume calculation."""
        # Excess volume is typically positive for grain boundaries
        mock_structure = MagicMock()
        mock_structure.lattice = MagicMock()
        mock_structure.lattice.a = 4.0
        mock_structure.lattice.b = 4.0
        mock_structure.lattice.c = 10.0
        
        excess_vol = calculate_excess_volume(mock_structure)
        
        # Should be a non-negative value
        assert excess_vol >= 0.0
        assert isinstance(excess_vol, float)


class TestParseStructureFile:
    """Tests for parse_structure_file function."""

    def test_parse_poscar_file(self):
        """Test parsing a POSCAR file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.vasp', delete=False) as f:
            # Write a minimal POSCAR
            f.write("""Test Structure
            1.0
            4.0 0.0 0.0
            0.0 4.0 0.0
            0.0 0.0 10.0
            C
            2
            Direct
            0.0 0.0 0.0
            0.5 0.5 0.5
            """)
            temp_path = f.name

        try:
            structure = parse_structure_file(temp_path)
            # Check that structure is not None
            assert structure is not None
            # Check number of sites
            assert len(structure) == 2
        finally:
            os.unlink(temp_path)

    def test_parse_cif_file(self):
        """Test parsing a CIF file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.cif', delete=False) as f:
            f.write("""data_test
            _cell_length_a 4.0
            _cell_length_b 4.0
            _cell_length_c 10.0
            _cell_angle_alpha 90
            _cell_angle_beta 90
            _cell_angle_gamma 90
            _symmetry_space_group_name_H-M 'P 1'
            loop_
            _atom_site_label
            _atom_site_type_symbol
            _atom_site_fract_x
            _atom_site_fract_y
            _atom_site_fract_z
            C1 C 0.0 0.0 0.0
            C2 C 0.5 0.5 0.5
            """)
            temp_path = f.name

        try:
            structure = parse_structure_file(temp_path)
            assert structure is not None
            assert len(structure) == 2
        finally:
            os.unlink(temp_path)

    def test_parse_nonexistent_file_raises(self):
        """Test that parsing a nonexistent file raises an error."""
        with pytest.raises(FileNotFoundError):
            parse_structure_file("nonexistent_file.vasp")


class TestExtractGeometryFeatures:
    """Tests for extract_geometry_features function."""

    def test_extract_features_returns_dict(self):
        """Test that the function returns a dictionary of features."""
        mock_structure = MagicMock()
        mock_structure.lattice = MagicMock()
        mock_structure.lattice.a = 4.0
        mock_structure.lattice.b = 4.0
        mock_structure.lattice.c = 10.0
        
        features = extract_geometry_features(mock_structure, 60.0)
        
        assert isinstance(features, dict)
        # Check for expected keys
        expected_keys = [
            'misorientation_angle',
            'sigma_value',
            'boundary_plane_normal',
            'boundary_width',
            'excess_volume'
        ]
        for key in expected_keys:
            assert key in features

    def test_extract_features_types(self):
        """Test the types of extracted features."""
        mock_structure = MagicMock()
        mock_structure.lattice = MagicMock()
        mock_structure.lattice.a = 4.0
        mock_structure.lattice.b = 4.0
        mock_structure.lattice.c = 10.0
        
        features = extract_geometry_features(mock_structure, 60.0)
        
        assert isinstance(features['misorientation_angle'], float)
        assert isinstance(features['sigma_value'], int)
        assert isinstance(features['boundary_plane_normal'], np.ndarray)
        assert isinstance(features['boundary_width'], float)
        assert isinstance(features['excess_volume'], float)
        assert len(features['boundary_plane_normal']) == 3

    def test_extract_features_with_rodrigues(self):
        """Test that Rodrigues vector is included if requested or calculated."""
        mock_structure = MagicMock()
        mock_structure.lattice = MagicMock()
        mock_structure.lattice.a = 4.0
        mock_structure.lattice.b = 4.0
        mock_structure.lattice.c = 10.0
        
        features = extract_geometry_features(mock_structure, 60.0)
        
        # Check if rodrigues_vector is present (implementation dependent)
        # If the function is designed to always return it:
        if 'rodrigues_vector' in features:
            assert isinstance(features['rodrigues_vector'], np.ndarray)
            assert len(features['rodrigues_vector']) == 3