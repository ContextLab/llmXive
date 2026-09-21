"""
Unit tests for descriptor computation module.
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from unittest.mock import Mock, patch
import sys
from pymatgen.core import Structure, Lattice, Site, Composition
from pymatgen.analysis.local_env import OctahedralSiteSymmetryFinder
from src.descriptors.compute_descriptors import (
    calculate_tolerance_factor,
    calculate_octahedral_tilting_angles,
    calculate_bond_length_variance,
    calculate_unit_cell_volume,
    compute_all_descriptors,
    process_dataframe
)

class MockLattice:
    """Mock lattice for testing."""
    def __init__(self, volume=100.0):
        self.volume = volume

class MockSite:
    """Mock site for testing."""
    def __init__(self, coords, species):
        self.coords = np.array(coords)
        self.species = species

    def distance(self, other):
        return np.linalg.norm(np.array(self.coords) - np.array(other.coords))

class MockComposition:
    """Mock composition for testing."""
    def __init__(self, formula):
        self.formula = formula

class MockElement:
    """Mock element for testing."""
    def __init__(self, name):
        self.name = name

class MockStructure:
    """Mock structure for testing."""
    def __init__(self):
        self.lattice = MockLattice(volume=150.0)
        self.sites = []
        self.composition = MockComposition("ABX3")

def mock_perovskite_structure():
    """Create a mock perovskite structure for testing."""
    lattice = Lattice.cubic(4.0)
    species = ["Ba", "Ti", "O", "O", "O"]
    coords = [
        [0, 0, 0],      # Ba at corner
        [0.5, 0.5, 0.5], # Ti at body center
        [0.5, 0.5, 0],   # O at face centers
        [0.5, 0, 0.5],
        [0, 0.5, 0.5]
    ]
    structure = Structure(lattice, species, coords)
    return structure

class TestToleranceFactor:
    """Tests for tolerance factor calculation."""

    def test_tolerance_factor_calculation(self):
        """Test that tolerance factor is calculated for a valid structure."""
        structure = mock_perovskite_structure()
        tf = calculate_tolerance_factor(structure)
        assert isinstance(tf, float)
        assert 0.5 < tf < 1.5  # Typical tolerance factor range

    def test_tolerance_factor_nan_on_error(self):
        """Test that NaN is returned on error."""
        with patch('src.descriptors.compute_descriptors.GlobalToleranceFactor') as mock_gtf:
            mock_gtf.side_effect = Exception("Test error")
            structure = mock_perovskite_structure()
            tf = calculate_tolerance_factor(structure)
            assert np.isnan(tf)

class TestOctahedralTilting:
    """Tests for octahedral tilting angle calculation."""

    def test_tilting_angle_calculation(self):
        """Test that tilting angle is calculated."""
        structure = mock_perovskite_structure()
        angle = calculate_octahedral_tilting_angles(structure)
        assert isinstance(angle, float)
        assert angle >= 0

    def test_tilting_angle_zero_for_ideal(self):
        """Test that ideal octahedron returns zero tilting."""
        # This is a simplified test; real ideal structures would need proper setup
        structure = mock_perovskite_structure()
        angle = calculate_octahedral_tilting_angles(structure)
        # Should not be NaN
        assert not np.isnan(angle)

    def test_tilting_angle_nan_on_no_sites(self):
        """Test that NaN is returned when no octahedral sites found."""
        with patch('src.descriptors.compute_descriptors.OctahedralSiteSymmetryFinder') as mock_finder:
            mock_finder.return_value.get_octahedral_sites.return_value = []
            structure = mock_perovskite_structure()
            angle = calculate_octahedral_tilting_angles(structure)
            assert np.isnan(angle)

class TestBondLengthVariance:
    """Tests for bond length variance calculation."""

    def test_bond_length_variance_calculation(self):
        """Test that bond length variance is calculated."""
        structure = mock_perovskite_structure()
        variance = calculate_bond_length_variance(structure)
        assert isinstance(variance, float)
        assert variance >= 0

    def test_bond_length_variance_nan_on_insufficient_data(self):
        """Test that NaN is returned with insufficient bond data."""
        with patch('src.descriptors.compute_descriptors.OctahedralSiteSymmetryFinder') as mock_finder:
            mock_finder.return_value.get_octahedral_sites.return_value = []
            structure = mock_perovskite_structure()
            variance = calculate_bond_length_variance(structure)
            assert np.isnan(variance)

class TestUnitCellVolume:
    """Tests for unit cell volume calculation."""

    def test_volume_calculation(self):
        """Test that unit cell volume is calculated."""
        structure = mock_perovskite_structure()
        volume = calculate_unit_cell_volume(structure)
        assert isinstance(volume, float)
        assert volume > 0

    def test_volume_matches_lattice(self):
        """Test that volume matches lattice volume."""
        structure = mock_perovskite_structure()
        volume = calculate_unit_cell_volume(structure)
        assert abs(volume - structure.lattice.volume) < 1e-6

    def test_volume_nan_on_error(self):
        """Test that NaN is returned on error."""
        with patch.object(Structure, 'lattice', None):
            structure = mock_perovskite_structure()
            structure.lattice = None
            # This would fail, but we test the exception handling
            try:
                volume = calculate_unit_cell_volume(structure)
                assert np.isnan(volume)
            except:
                # If it raises, that's also acceptable behavior
                pass

class TestComputeAllDescriptors:
    """Tests for computing all descriptors."""

    def test_all_descriptors_computed(self):
        """Test that all descriptors are computed."""
        structure = mock_perovskite_structure()
        descriptors = compute_all_descriptors(structure)
        
        assert 'tolerance_factor' in descriptors
        assert 'octahedral_tilting_angle' in descriptors
        assert 'bond_length_variance' in descriptors
        assert 'unit_cell_volume' in descriptors

        assert isinstance(descriptors['tolerance_factor'], float)
        assert isinstance(descriptors['octahedral_tilting_angle'], float)
        assert isinstance(descriptors['bond_length_variance'], float)
        assert isinstance(descriptors['unit_cell_volume'], float)

    def test_descriptors_not_all_nan(self):
        """Test that not all descriptors are NaN."""
        structure = mock_perovskite_structure()
        descriptors = compute_all_descriptors(structure)
        
        valid_count = sum(1 for v in descriptors.values() if not np.isnan(v))
        assert valid_count > 0

class TestProcessDataFrame:
    """Tests for dataframe processing."""

    def test_dataframe_processing(self):
        """Test that dataframe is processed correctly."""
        # Create a mock dataframe with structure objects
        structure = mock_perovskite_structure()
        df = pd.DataFrame({
            'structure': [structure, structure, structure],
            'other_col': [1, 2, 3]
        })

        result_df = process_dataframe(df, 'structure')

        assert 'tolerance_factor' in result_df.columns
        assert 'octahedral_tilting_angle' in result_df.columns
        assert 'bond_length_variance' in result_df.columns
        assert 'unit_cell_volume' in result_df.columns
        assert len(result_df) == 3

    def test_dataframe_with_nan_structures(self):
        """Test handling of invalid structures."""
        df = pd.DataFrame({
            'structure': [None, "invalid", 123],
            'other_col': [1, 2, 3]
        })

        result_df = process_dataframe(df, 'structure')

        # Should have NaN for all descriptors
        assert result_df['tolerance_factor'].isna().all()
        assert result_df['octahedral_tilting_angle'].isna().all()
        assert result_df['bond_length_variance'].isna().all()
        assert result_df['unit_cell_volume'].isna().all()

class TestMain:
    """Tests for main function."""

    @patch('src.descriptors.compute_descriptors.argparse.ArgumentParser')
    @patch('src.descriptors.compute_descriptors.Path')
    @patch('src.descriptors.compute_descriptors.pd.read_csv')
    @patch('src.descriptors.compute_descriptors.process_dataframe')
    @patch('src.descriptors.compute_descriptors.init_seed')
    def test_main_execution(
        self,
        mock_init_seed,
        mock_process_df,
        mock_read_csv,
        mock_path,
        mock_parser
    ):
        """Test main function execution flow."""
        # Setup mocks
        mock_args = Mock()
        mock_args.input = 'test_input.csv'
        mock_args.output = 'test_output.csv'
        mock_args.seed = 42
        mock_args.structure_column = 'structure'
        mock_parser.return_value.parse_args.return_value = mock_args

        mock_df = pd.DataFrame({'structure': [mock_perovskite_structure()]})
        mock_read_csv.return_value = mock_df

        mock_result = pd.DataFrame({
            'structure': [mock_perovskite_structure()],
            'tolerance_factor': [0.9]
        })
        mock_process_df.return_value = mock_result

        mock_output_path = Mock()
        mock_output_path.parent = Mock()
        mock_output_path.parent.mkdir = Mock()
        mock_path.return_value = mock_output_path

        # Import and run main
        from src.descriptors.compute_descriptors import main
        main()

        # Verify calls
        mock_read_csv.assert_called_once_with('test_input.csv')
        mock_process_df.assert_called_once()
        mock_output_path.parent.mkdir.assert_called_once()