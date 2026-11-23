import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from unittest.mock import Mock, patch
import sys
import os

# Add the code directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.descriptors.compute_descriptors import (
    calculate_tolerance_factor,
    calculate_octahedral_tilting_angles,
    calculate_bond_length_variance,
    calculate_unit_cell_volume,
    compute_all_descriptors,
    process_dataframe,
    main
)

# Mock pymatgen classes for testing
class MockLattice:
    def __init__(self, volume=100.0):
        self.volume = volume

class MockSite:
    def __init__(self, species_string, coords):
        self.species_string = species_string
        self.coords = coords
        self.distance = lambda other: np.linalg.norm(np.array(self.coords) - np.array(other.coords))

class MockStructure:
    def __init__(self, sites, lattice=None):
        self.sites = sites
        self.lattice = lattice or MockLattice()
        self.composition = MockComposition(sites)
    
    def __iter__(self):
        return iter(self.sites)
    
    def __getitem__(self, idx):
        return self.sites[idx]
    
    def __len__(self):
        return len(self.sites)

class MockComposition:
    def __init__(self, sites):
        elements = {}
        for site in sites:
            el = site.species_string
            elements[el] = elements.get(el, 0) + 1
        self.elements = [MockElement(el, count) for el, count in elements.items()]

class MockElement:
    def __init__(self, symbol, count):
        self.symbol = symbol
        self.count = count
        # Mock ionic radii
        self.ionic_radius = {
            'Ti': 0.605, 'O': 1.40, 'Pb': 1.19, 'I': 2.20,
            'Ba': 1.35, 'Zr': 0.72, 'Ca': 1.00, 'Sr': 1.18
        }.get(symbol, 1.0)
        self.X = {
            'O': 3.44, 'F': 3.98, 'Cl': 3.16, 'Br': 2.96, 'I': 2.66,
            'Ti': 1.54, 'Pb': 2.33, 'Ba': 0.89, 'Zr': 1.33, 'Ca': 1.00, 'Sr': 0.95
        }.get(symbol, 1.0)

@pytest.fixture
def mock_perovskite_structure():
    # Create a mock perovskite structure: ABX3
    # A=Ba, B=Ti, X=O
    sites = [
        MockSite('Ba', [0, 0, 0]),
        MockSite('Ti', [0.5, 0.5, 0.5]),
        MockSite('O', [0.5, 0.5, 0]),
        MockSite('O', [0.5, 0, 0.5]),
        MockSite('O', [0, 0.5, 0.5]),
    ]
    return MockStructure(sites)

class TestToleranceFactor:
    def test_calculate_tolerance_factor(self, mock_perovskite_structure):
        # Test with a known perovskite (BaTiO3)
        # Expected t is around 1.0
        with patch('src.descriptors.compute_descriptors.PmgToleranceFactor', None):
            t = calculate_tolerance_factor(mock_perovskite_structure)
            assert isinstance(t, float)
            assert 0.5 < t < 1.5  # Reasonable range for perovskites

class TestOctahedralTilting:
    def test_calculate_octahedral_tilting_angles(self, mock_perovskite_structure):
        # Mock the OctahedralSiteSymmetryFinder to return a fixed angle
        with patch('src.descriptors.compute_descriptors.OctahedralSiteSymmetryFinder') as MockFinder:
            mock_finder_instance = Mock()
            mock_finder_instance.tilting_angles = [10.0, 10.0, 10.0]
            MockFinder.return_value = mock_finder_instance
            
            angle = calculate_octahedral_tilting_angles(mock_perovskite_structure)
            assert isinstance(angle, float)
            assert angle == 10.0

class TestBondLengthVariance:
    def test_calculate_bond_length_variance(self, mock_perovskite_structure):
        # Mock the structure to have known bond lengths
        # We need to mock the distance calculation
        with patch.object(MockSite, 'distance', return_value=2.0):
            variance = calculate_bond_length_variance(mock_perovskite_structure)
            assert isinstance(variance, float)
            # If all distances are 2.0, variance should be 0
            assert variance == 0.0

class TestUnitCellVolume:
    def test_calculate_unit_cell_volume(self, mock_perovskite_structure):
        volume = calculate_unit_cell_volume(mock_perovskite_structure)
        assert isinstance(volume, float)
        assert volume == 100.0  # From MockLattice

class TestComputeAllDescriptors:
    def test_compute_all_descriptors(self, mock_perovskite_structure):
        with patch('src.descriptors.compute_descriptors.OctahedralSiteSymmetryFinder') as MockFinder:
            mock_finder_instance = Mock()
            mock_finder_instance.tilting_angles = [10.0]
            MockFinder.return_value = mock_finder_instance
            
            with patch.object(MockSite, 'distance', return_value=2.0):
                descriptors = compute_all_descriptors(mock_perovskite_structure)
                
                assert 'tolerance_factor' in descriptors
                assert 'octahedral_tilting_angle' in descriptors
                assert 'bond_length_variance' in descriptors
                assert 'unit_cell_volume' in descriptors
                
                assert isinstance(descriptors['tolerance_factor'], float)
                assert isinstance(descriptors['octahedral_tilting_angle'], float)
                assert isinstance(descriptors['bond_length_variance'], float)
                assert isinstance(descriptors['unit_cell_volume'], float)

class TestProcessDataFrame:
    def test_process_dataframe(self, mock_perovskite_structure):
        # Create a mock dataframe
        df = pd.DataFrame({
            'structure': [mock_perovskite_structure, mock_perovskite_structure],
            'other_col': [1, 2]
        })
        
        with patch('src.descriptors.compute_descriptors.OctahedralSiteSymmetryFinder') as MockFinder:
            mock_finder_instance = Mock()
            mock_finder_instance.tilting_angles = [10.0]
            MockFinder.return_value = mock_finder_instance
            
            with patch.object(MockSite, 'distance', return_value=2.0):
                result_df = process_dataframe(df)
                
                assert 'tolerance_factor' in result_df.columns
                assert 'octahedral_tilting_angle' in result_df.columns
                assert 'bond_length_variance' in result_df.columns
                assert 'unit_cell_volume' in result_df.columns
                assert len(result_df) == 2

class TestMain:
    def test_main(self, tmp_path):
        input_file = tmp_path / "input.csv"
        output_file = tmp_path / "output.csv"
        
        # Create a mock input file
        df = pd.DataFrame({'structure': [MockStructure([])]})
        df.to_csv(input_file, index=False)
        
        # Mock the process_dataframe function
        with patch('src.descriptors.compute_descriptors.process_dataframe') as mock_process:
            mock_process.return_value = pd.DataFrame({'structure': [MockStructure([])], 'tolerance_factor': [1.0]})
            
            # Call main
            sys.argv = ['compute_descriptors.py', '--input', str(input_file), '--output', str(output_file)]
            main()
            
            # Check if output file was created
            assert output_file.exists()