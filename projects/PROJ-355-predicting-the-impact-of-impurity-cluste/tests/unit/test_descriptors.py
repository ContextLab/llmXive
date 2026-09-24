"""
Unit tests for code/data/descriptors.py
"""
import pytest
import numpy as np
from pymatgen.core import Structure, Lattice
from data.descriptors import get_interface_atoms, compute_rdf_peak

def test_get_interface_atoms():
    """Test interface atom selection logic."""
    # Create a simple cubic structure
    lattice = Lattice.cubic(3.0)
    species = ["Fe", "Fe", "Fe", "Fe"]
    coords = [[0, 0, 0], [0.5, 0.5, 0], [0.5, 0, 0.5], [0, 0.5, 0.5]]
    structure = Structure(lattice, species, coords)

    # Mock interface plane (z=0.5)
    atoms = get_interface_atoms(structure, plane_normal=[0, 0, 1], plane_offset=0.5, cutoff=0.5)
    assert isinstance(atoms, list)

def test_compute_rdf_peak_empty():
    """Test RDF computation with empty atom list."""
    positions = np.array([]).reshape(0, 3)
    result = compute_rdf_peak(positions)
    assert result is None
