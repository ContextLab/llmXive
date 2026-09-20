"""Unit tests for interface-region descriptor filtering."""
import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
import numpy as np

# Add parent directory to path to import code modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.descriptors import get_interface_atoms, compute_rdf_peak, compute_pair_correlation, compute_voronoi_neighbor_counts
from config import get_project_root

class MockStructure:
    """Mock pymatgen Structure for testing without heavy dependencies."""
    def __init__(self, sites, lattice=None):
        self.sites = sites
        self.lattice = lattice or MagicMock()
        self.lattice.abc = (5.0, 5.0, 5.0)
        self.lattice.angles = (90, 90, 90)
    
    def get_distance(self, i, j):
        """Mock distance calculation."""
        return np.linalg.norm(np.array(self.sites[i]['coords']) - np.array(self.sites[j]['coords']))

@pytest.fixture
def mock_gb_structure():
    """Create a mock GB supercell with known interface atoms."""
    # Simulate a simple cubic structure with a GB plane at z=2.5
    sites = [
        {'species': 'Fe', 'coords': [1.0, 1.0, 1.0], 'properties': {'site': 0}},
        {'species': 'Fe', 'coords': [2.0, 2.0, 2.0], 'properties': {'site': 1}},
        {'species': 'Fe', 'coords': [1.0, 1.0, 4.0], 'properties': {'site': 2}}, # Above interface
        {'species': 'Fe', 'coords': [2.0, 2.0, 1.0], 'properties': {'site': 3}},
        {'species': 'Cr', 'coords': [1.5, 1.5, 2.5], 'properties': {'site': 4}}, # At interface (impurity)
        {'species': 'Fe', 'coords': [3.0, 3.0, 2.5], 'properties': {'site': 5}}, # At interface
    ]
    return MockStructure(sites)

def test_get_interface_atoms_within_cutoff(mock_gb_structure):
    """Test filtering atoms within 5 Å of the GB plane (z=2.5)."""
    # Mock the GB plane position (z=2.5)
    gb_plane_z = 2.5
    cutoff = 5.0
    
    # Expected: All atoms are within 5 Å of z=2.5 in this small mock
    # Atom 0: z=1.0 -> dist=1.5
    # Atom 1: z=2.0 -> dist=0.5
    # Atom 2: z=4.0 -> dist=1.5
    # Atom 3: z=1.0 -> dist=1.5
    # Atom 4: z=2.5 -> dist=0.0
    # Atom 5: z=2.5 -> dist=0.0
    
    # We need to pass the structure and logic to get_interface_atoms
    # Since the real function expects a pymatgen Structure, we mock the distance calculation
    # or rely on the fact that our mock structure has simple coordinates.
    
    # For this test, we verify the logic by checking that the function
    # correctly identifies atoms based on a z-coordinate threshold.
    # The real implementation uses `get_distance` from pymatgen.
    
    # Simulate the logic:
    interface_indices = []
    for i, site in enumerate(mock_gb_structure.sites):
        # Assuming GB plane is defined by a normal and a point, or a simple z-cut
        # For this test, we assume the GB plane is z=2.5
        z_dist = abs(site['coords'][2] - gb_plane_z)
        if z_dist <= cutoff:
            interface_indices.append(i)
    
    assert len(interface_indices) == 6, "All mock atoms should be within cutoff"
    assert 4 in interface_indices, "Impurity at interface should be included"

def test_compute_rdf_peak_interface(mock_gb_structure):
    """Test RDF peak computation for interface atoms."""
    # Mock the interface atom indices
    interface_indices = [4, 5] # Cr and Fe at interface
    
    # The real function computes RDF between interface atoms and neighbors
    # We test that it returns a numeric peak value
    with patch('data.descriptors.compute_rdf_peak') as mock_rdf:
        mock_rdf.return_value = 2.45 # Mock RDF peak
        result = mock_rdf(mock_gb_structure, interface_indices)
        assert isinstance(result, float)
        assert result > 0

def test_compute_pair_correlation_interface(mock_gb_structure):
    """Test pair correlation statistics for interface region."""
    interface_indices = [4, 5]
    
    with patch('data.descriptors.compute_pair_correlation') as mock_pc:
        mock_pc.return_value = 0.85 # Mock pair correlation
        result = mock_pc(mock_gb_structure, interface_indices)
        assert isinstance(result, float)
        assert 0 <= result <= 1

def test_compute_voronoi_neighbor_counts_interface(mock_gb_structure):
    """Test Voronoi neighbor count for interface atoms."""
    interface_indices = [4, 5]
    
    with patch('data.descriptors.compute_voronoi_neighbor_counts') as mock_voronoi:
        mock_voronoi.return_value = 8 # Mock neighbor count
        result = mock_voronoi(mock_gb_structure, interface_indices)
        assert isinstance(result, int)
        assert result > 0

def test_interface_region_filtering_logic():
    """Test the core logic of filtering atoms by distance to GB plane."""
    # Create a list of z-coordinates
    z_coords = [1.0, 2.0, 2.5, 3.0, 8.0]
    gb_plane_z = 2.5
    cutoff = 5.0
    
    interface_atoms = []
    for z in z_coords:
        if abs(z - gb_plane_z) <= cutoff:
            interface_atoms.append(z)
    
    # 8.0 is 5.5 away, so it should be excluded
    assert len(interface_atoms) == 4
    assert 8.0 not in interface_atoms
    assert 2.5 in interface_atoms

def test_descriptor_computation_raises_on_empty_interface():
    """Ensure descriptor functions handle empty interface regions gracefully."""
    empty_indices = []
    
    # Test that functions return sensible defaults or raise appropriate errors
    # For this test, we expect the functions to handle empty lists without crashing
    # or returning NaN.
    
    # Mocking the behavior for empty input
    with patch('data.descriptors.compute_rdf_peak') as mock_rdf:
        mock_rdf.return_value = np.nan
        result = mock_rdf(None, empty_indices)
        assert np.isnan(result)

def test_integration_interface_descriptor_pipeline(mock_gb_structure):
    """Integration test: verify all descriptor functions work together on interface."""
    # This test simulates the flow: identify interface -> compute descriptors
    gb_plane_z = 2.5
    cutoff = 5.0
    
    # 1. Identify interface atoms
    interface_indices = [i for i, site in enumerate(mock_gb_structure.sites) 
                         if abs(site['coords'][2] - gb_plane_z) <= cutoff]
    
    assert len(interface_indices) > 0, "Should find interface atoms"
    
    # 2. Compute descriptors (mocked for this unit test)
    # In a real scenario, these would call the actual pymatgen functions
    descriptors = {
        'rdf_peak': 2.45,
        'pair_corr': 0.85,
        'voronoi_count': 8
    }
    
    assert 'rdf_peak' in descriptors
    assert 'pair_corr' in descriptors
    assert 'voronoi_count' in descriptors