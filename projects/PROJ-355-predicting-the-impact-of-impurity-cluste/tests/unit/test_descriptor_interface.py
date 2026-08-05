"""
Unit test for interface-region descriptor filtering.

This test verifies that descriptors are correctly computed for the 
interface region of grain boundary supercells.
"""
import pytest
import numpy as np
from pathlib import Path
import sys
import os

# Add code to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from data.descriptors import get_interface_atoms, compute_rdf_peak, compute_pair_correlation

@pytest.fixture
def mock_gb_structure():
    """Create a mock grain boundary structure for testing.
    
    Returns a dictionary simulating the structure of atoms with
    distance_from_plane attribute to test filtering logic.
    """
    return {
        "atoms": [
            {"type": "Fe", "x": 0.0, "y": 0.0, "z": 0.0, "distance_from_plane": 0.1},
            {"type": "Fe", "x": 1.0, "y": 0.0, "z": 0.0, "distance_from_plane": 0.2},
            {"type": "Cr", "x": 0.5, "y": 0.5, "z": 0.0, "distance_from_plane": 0.05},
            {"type": "Fe", "x": 2.0, "y": 0.0, "z": 0.0, "distance_from_plane": 1.5},
            {"type": "Fe", "x": 3.0, "y": 0.0, "z": 0.0, "distance_from_plane": 2.0},
        ],
        "interface_plane_z": 0.0,
        "interface_thickness": 0.5
    }

def test_get_interface_atoms(mock_gb_structure):
    """Test that interface atoms are correctly identified."""
    interface_atoms = get_interface_atoms(
        mock_gb_structure["atoms"],
        mock_gb_structure["interface_plane_z"],
        mock_gb_structure["interface_thickness"]
    )
    
    # Should include atoms within the interface thickness (0.5)
    # Atoms with distance_from_plane: 0.1, 0.2, 0.05 are within 0.5
    # Atom with 1.5 and 2.0 are outside
    assert len(interface_atoms) == 3, f"Expected 3 interface atoms, got {len(interface_atoms)}"
    
    # All returned atoms should be within the interface region
    for atom in interface_atoms:
        distance = abs(atom["distance_from_plane"])
        assert distance <= mock_gb_structure["interface_thickness"], \
            f"Atom at distance {distance} exceeds thickness {mock_gb_structure['interface_thickness']}"

def test_compute_rdf_peak(mock_gb_structure):
    """Test RDF peak computation on interface atoms."""
    interface_atoms = get_interface_atoms(
        mock_gb_structure["atoms"],
        mock_gb_structure["interface_plane_z"],
        mock_gb_structure["interface_thickness"]
    )
    
    # Convert mock atoms to a format suitable for RDF computation
    # The function expects coordinates and species
    coords = np.array([[a["x"], a["y"], a["z"]] for a in interface_atoms])
    species = [a["type"] for a in interface_atoms]
    
    rdf_peak, rdf_data = compute_rdf_peak(coords, species, r_max=5.0, dr=0.1)
    
    # RDF peak should be a positive value (or 0 if no neighbors found in range)
    assert rdf_peak >= 0
    assert len(rdf_data) > 0

def test_compute_pair_correlation(mock_gb_structure):
    """Test pair correlation computation on interface atoms."""
    interface_atoms = get_interface_atoms(
        mock_gb_structure["atoms"],
        mock_gb_structure["interface_plane_z"],
        mock_gb_structure["interface_thickness"]
    )
    
    coords = np.array([[a["x"], a["y"], a["z"]] for a in interface_atoms])
    species = [a["type"] for a in interface_atoms]
    
    pair_corr = compute_pair_correlation(coords, species)
    
    # Should return a dictionary with correlation values
    assert isinstance(pair_corr, dict)
    assert len(pair_corr) > 0

def test_get_interface_atoms_empty_if_thin(mock_gb_structure):
    """Test filtering when thickness is too small to include any atoms."""
    # Set thickness to 0.01, no atoms are closer than 0.05
    interface_atoms = get_interface_atoms(
        mock_gb_structure["atoms"],
        mock_gb_structure["interface_plane_z"],
        0.01
    )
    
    assert len(interface_atoms) == 0

def test_get_interface_atoms_all_if_thick(mock_gb_structure):
    """Test filtering when thickness includes all atoms."""
    # Set thickness to 3.0, all atoms should be included
    interface_atoms = get_interface_atoms(
        mock_gb_structure["atoms"],
        mock_gb_structure["interface_plane_z"],
        3.0
    )
    
    assert len(interface_atoms) == len(mock_gb_structure["atoms"])