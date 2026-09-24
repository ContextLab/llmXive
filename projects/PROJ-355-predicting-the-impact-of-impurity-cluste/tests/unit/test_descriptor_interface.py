"""
Unit test for interface-region descriptor filtering.
"""
import pytest
import numpy as np
from pymatgen.core import Structure, Lattice
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from data.descriptors import get_interface_atoms

def test_interface_filtering():
    """
    Test that get_interface_atoms correctly filters atoms based on distance to plane.
    """
    # Create a simple structure
    lattice = Lattice.cubic(4.0)
    species = ["Fe"] * 8
    coords = [
        [0, 0, 0], [0.5, 0.5, 0], [0.5, 0, 0.5], [0, 0.5, 0.5],
        [0.25, 0.25, 0.25], [0.75, 0.75, 0.25], [0.75, 0.25, 0.75], [0.25, 0.75, 0.75]
    ]
    structure = Structure(lattice, species, coords)

    # Define interface plane (e.g., z = 0.5)
    # We expect atoms near z=0.5 to be selected
    interface_atoms = get_interface_atoms(structure, plane_normal=[0, 0, 1], plane_offset=0.5, cutoff=0.25)

    # Verify we got some atoms
    assert len(interface_atoms) > 0, "No interface atoms found"

    # Verify all returned atoms are within the cutoff distance
    for atom in interface_atoms:
        # Calculate distance to plane
        z_coord = atom.frac_coords[2]
        dist = abs(z_coord - 0.5)
        assert dist <= 0.25 + 1e-6, f"Atom {atom} is outside cutoff"
