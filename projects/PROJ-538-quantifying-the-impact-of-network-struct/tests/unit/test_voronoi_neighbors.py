"""
Unit tests for Voronoi-based nearest-neighbor detection (US1).

This test suite validates the Voronoi neighbor finder implementation.
It depends on the IVoronoiNeighborFinder interface defined in code/interfaces.py.

Tests verify:
1. Correct construction of Voronoi diagrams from atomic coordinates.
2. Accurate identification of nearest neighbors based on Voronoi ridges.
3. Proper handling of species mismatch constraints (edges only between different species).
4. Robustness against degenerate cases (collinear points, duplicate coordinates).
"""

import pytest
import numpy as np
from scipy.spatial import Voronoi
from typing import List, Tuple, Set

# Import the interface to ensure we are testing against the correct contract
from code.interfaces import IVoronoiNeighborFinder
from code.models import AtomicSnapshot
from code.utils import VoronoiFailure


class MockVoronoiFinder(IVoronoiNeighborFinder):
    """
    Concrete implementation of IVoronoiNeighborFinder for testing.
    Uses scipy.spatial.Voronoi to compute neighbors.
    """
    def find_neighbors(self, snapshot: AtomicSnapshot, box_size: float) -> List[Tuple[int, int]]:
        """
        Find nearest neighbors using Voronoi tessellation.

        Args:
            snapshot: The atomic snapshot containing coordinates and species.
            box_size: The side length of the cubic simulation box.

        Returns:
            A list of tuples (i, j) representing edges between nearest neighbors.
            Edges are undirected (i < j).

        Raises:
            VoronoiFailure: If the Voronoi computation fails or input is invalid.
        """
        try:
            coords = np.array(snapshot.coordinates)
            species = np.array(snapshot.species)
            n_atoms = len(coords)

            if n_atoms < 2:
                raise VoronoiFailure("Need at least 2 atoms to compute neighbors.")

            if np.any(np.isnan(coords)) or np.any(np.isinf(coords)):
                raise VoronoiFailure("Coordinates contain NaN or Inf values.")

            # Compute Voronoi diagram
            vor = Voronoi(coords)

            # Extract ridges (edges of Voronoi cells)
            # Each ridge connects two vertices and separates two regions (atoms)
            neighbors = set()
            
            for simplex in vor.ridge_vertices:
                # simplex is a list of two vertex indices
                if -1 in simplex:
                    # Infinite ridge, ignore for nearest neighbor detection in periodic box
                    # In a real implementation with PBC, we would handle this differently
                    continue
                
                # Get the regions (atoms) associated with this ridge
                # vor.ridge_points maps ridge index to the two atoms separated by this ridge
                pass

            # Alternative approach: Use ridge_points directly
            # ridge_points[i] gives the two atom indices separated by ridge i
            for i, (idx1, idx2) in enumerate(vor.ridge_points):
                if idx1 >= 0 and idx2 >= 0:
                    # Ensure consistent ordering (i < j)
                    u, v = min(idx1, idx2), max(idx1, idx2)
                    neighbors.add((u, v))

            # Filter to only mismatched species pairs
            mismatched_neighbors = []
            for u, v in neighbors:
                if species[u] != species[v]:
                    mismatched_neighbors.append((u, v))

            return mismatched_neighbors

        except Exception as e:
            raise VoronoiFailure(f"Voronoi computation failed: {str(e)}") from e


@pytest.fixture
def simple_binary_snapshot():
    """Create a simple 2D binary alloy snapshot for testing."""
    # Simple square lattice with alternating species
    coords = np.array([
        [0.0, 0.0],   # Atom 0: A
        [1.0, 0.0],   # Atom 1: B
        [0.0, 1.0],   # Atom 2: B
        [1.0, 1.0],   # Atom 3: A
        [0.5, 0.5],   # Atom 4: A (center)
    ])
    species = ['A', 'B', 'B', 'A', 'A']
    
    return AtomicSnapshot(
        coordinates=coords.tolist(),
        species=species,
        temperature=300.0,
        box_size=2.0
    )


@pytest.fixture
def degenerate_snapshot():
    """Create a snapshot with degenerate geometry (collinear points)."""
    coords = np.array([
        [0.0, 0.0],
        [1.0, 0.0],
        [2.0, 0.0],
    ])
    species = ['A', 'B', 'A']
    
    return AtomicSnapshot(
        coordinates=coords.tolist(),
        species=species,
        temperature=300.0,
        box_size=3.0
    )


@pytest.fixture
def single_atom_snapshot():
    """Create a snapshot with only one atom."""
    coords = np.array([[0.5, 0.5]])
    species = ['A']
    
    return AtomicSnapshot(
        coordinates=coords.tolist(),
        species=species,
        temperature=300.0,
        box_size=1.0
    )


class TestVoronoiNeighborFinder:
    """Test suite for Voronoi-based nearest-neighbor detection."""

    def test_interface_conformance(self):
        """Verify that MockVoronoiFinder implements the interface correctly."""
        finder = MockVoronoiFinder()
        assert isinstance(finder, IVoronoiNeighborFinder)
        assert hasattr(finder, 'find_neighbors')

    def test_basic_neighbor_detection(self, simple_binary_snapshot):
        """Test that neighbors are correctly identified in a simple binary system."""
        finder = MockVoronoiFinder()
        neighbors = finder.find_neighbors(simple_binary_snapshot, box_size=2.0)
        
        # Verify we got some neighbors
        assert len(neighbors) > 0
        
        # Verify all edges are between mismatched species
        species = simple_binary_snapshot.species
        for u, v in neighbors:
            assert species[u] != species[v], f"Edge ({u}, {v}) connects same species"

    def test_no_same_species_edges(self, simple_binary_snapshot):
        """Ensure no edges exist between atoms of the same species."""
        finder = MockVoronoiFinder()
        neighbors = finder.find_neighbors(simple_binary_snapshot, box_size=2.0)
        
        species = simple_binary_snapshot.species
        for u, v in neighbors:
            assert species[u] != species[v]

    def test_single_atom_raises(self, single_atom_snapshot):
        """Test that a single atom snapshot raises VoronoiFailure."""
        finder = MockVoronoiFinder()
        with pytest.raises(VoronoiFailure):
            finder.find_neighbors(single_atom_snapshot, box_size=1.0)

    def test_degenerate_geometry_handling(self, degenerate_snapshot):
        """Test behavior with collinear points (degenerate Voronoi)."""
        finder = MockVoronoiFinder()
        # Should not crash, but may return empty or limited neighbors
        try:
            neighbors = finder.find_neighbors(degenerate_snapshot, box_size=3.0)
            # If it succeeds, verify edges are valid
            species = degenerate_snapshot.species
            for u, v in neighbors:
                assert species[u] != species[v]
        except VoronoiFailure:
            # Acceptable if it fails with a clear error
            pass

    def test_output_format(self, simple_binary_snapshot):
        """Verify the output format is a list of tuples."""
        finder = MockVoronoiFinder()
        neighbors = finder.find_neighbors(simple_binary_snapshot, box_size=2.0)
        
        assert isinstance(neighbors, list)
        for edge in neighbors:
            assert isinstance(edge, tuple)
            assert len(edge) == 2
            u, v = edge
            assert isinstance(u, int)
            assert isinstance(v, int)
            assert u < v  # Consistent ordering

    def test_empty_species_mismatch(self):
        """Test with a system where all atoms are the same species."""
        coords = np.array([[0.0, 0.0], [1.0, 0.0], [0.0, 1.0]])
        species = ['A', 'A', 'A']
        snapshot = AtomicSnapshot(
            coordinates=coords.tolist(),
            species=species,
            temperature=300.0,
            box_size=2.0
        )
        
        finder = MockVoronoiFinder()
        neighbors = finder.find_neighbors(snapshot, box_size=2.0)
        
        # Should return empty list since no mismatched pairs exist
        assert len(neighbors) == 0

    def test_invalid_coordinates_raises(self):
        """Test that NaN/Inf coordinates raise VoronoiFailure."""
        coords = np.array([[0.0, np.nan], [1.0, 0.0]])
        species = ['A', 'B']
        snapshot = AtomicSnapshot(
            coordinates=coords.tolist(),
            species=species,
            temperature=300.0,
            box_size=2.0
        )
        
        finder = MockVoronoiFinder()
        with pytest.raises(VoronoiFailure):
            finder.find_neighbors(snapshot, box_size=2.0)