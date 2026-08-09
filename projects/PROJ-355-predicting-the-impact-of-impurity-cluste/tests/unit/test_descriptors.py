"""
Unit tests for descriptor computation module.
"""
import pytest
import numpy as np
from pathlib import Path
import pandas as pd

from code.data.descriptors import (
    get_interface_atoms,
    compute_rdf_peak,
    compute_pair_correlation,
    compute_voronoi_neighbor_counts,
    run_descriptor_computation
)
from pymatgen.core import Structure, Lattice

def test_get_interface_atoms():
    """Test interface atom identification."""
    # Create a simple cubic structure
    lattice = Lattice.cubic(3.0)
    coords = [
        [0.0, 0.0, 0.0],
        [0.5, 0.5, 0.5],
        [0.0, 0.0, 0.1],  # Close to z=0 plane
        [0.0, 0.0, 0.9],  # Close to z=0 plane (periodic)
        [0.5, 0.5, 0.5]   # Far from plane
    ]
    species = ["Fe"] * 5
    structure = Structure(lattice, species, coords)

    # Plane at z=0, cutoff 5.0 Å (which is ~1.66 in fractional for 3.0 Å lattice)
    normal = np.array([0, 0, 1])
    dist = 0.0

    interface = get_interface_atoms(structure, normal, dist)

    # Should include atoms close to z=0
    assert len(interface) >= 2
    assert 0 in interface or 2 in interface  # At least one close atom

def test_compute_pair_correlation_empty():
    """Test pair correlation with no interface atoms."""
    from pymatgen.core import Structure, Lattice

    lattice = Lattice.cubic(3.0)
    coords = [[0.0, 0.0, 0.0]]
    species = ["Fe"]
    structure = Structure(lattice, species, coords)

    result = compute_pair_correlation(structure, [], "Cr")
    assert result == 0.0

def test_compute_voronoi_neighbor_counts_empty():
    """Test Voronoi neighbor count with no interface atoms."""
    from pymatgen.core import Structure, Lattice

    lattice = Lattice.cubic(3.0)
    coords = [[0.0, 0.0, 0.0]]
    species = ["Fe"]
    structure = Structure(lattice, species, coords)

    result = compute_voronoi_neighbor_counts(structure, [], "Cr")
    assert result == 0

def test_run_descriptor_computation_structure():
    """Test the full descriptor computation pipeline returns correct structure."""
    from pymatgen.core import Structure, Lattice

    # Create a minimal test structure
    lattice = Lattice.cubic(4.0)
    coords = [
        [0.0, 0.0, 0.0],
        [0.5, 0.5, 0.5],
        [0.0, 0.0, 0.1],
        [0.0, 0.0, 0.9]
    ]
    species = ["Fe", "Fe", "Cr", "Cr"]
    structure = Structure(lattice, species, coords)

    normal = np.array([0, 0, 1])
    dist = 0.0

    result = run_descriptor_computation(
        structure=structure,
        impurity_species="Cr",
        gb_plane_normal=normal,
        gb_plane_dist=dist,
        alloy_system_id="BCC_Cr"
    )

    assert 'species' in result
    assert 'alloy_system_id' in result
    assert 'rdf_peak' in result
    assert 'pair_corr' in result
    assert 'voronoi_count' in result
    assert result['alloy_system_id'] == "BCC_Cr"
    assert result['species'] == "Cr"
    assert isinstance(result['rdf_peak'], float)
    assert isinstance(result['pair_corr'], float)
    assert isinstance(result['voronoi_count'], int)
