"""
Unit tests for the GB Builder module.
"""
import unittest
import tempfile
import os
from pathlib import Path
from pymatgen.core import Structure, Lattice
import numpy as np

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
from data.gb_builder import build_gb_supercell, insert_impurity, _identify_interface_atoms

class TestGBBuilder(unittest.TestCase):

    def setUp(self):
        # Create a simple BCC Iron structure for testing
        lattice = Lattice.cubic(2.86) # Fe lattice constant
        coords = [[0, 0, 0], [0.5, 0.5, 0.5]]
        species = ["Fe", "Fe"]
        self.bulk_structure = Structure(lattice, species, coords)

    def test_build_gb_supercell(self):
        """Test that GB supercell is built and has more atoms than bulk."""
        gb_structure = build_gb_supercell(self.bulk_structure, "Cr", "test_001")
        self.assertIsNotNone(gb_structure)
        # Supercell creation should increase atom count
        # Bulk has 2 atoms. Supercell (2x2x2) has 16. GB split might keep similar count or slightly different.
        self.assertGreater(len(gb_structure), 2)

    def test_insert_impurity(self):
        """Test that impurity is inserted into the structure."""
        gb_structure = build_gb_supercell(self.bulk_structure, "Cr", "test_001")
        
        # Check if Cr is present
        species_list = [str(site.species_string) for site in gb_structure]
        self.assertIn("Cr", species_list)

    def test_interface_identification(self):
        """Test that interface atoms are identified."""
        gb_structure = build_gb_supercell(self.bulk_structure, "Cr", "test_001")
        indices = _identify_interface_atoms(gb_structure)
        
        # Should find some atoms in the interface region
        self.assertIsInstance(indices, list)
        # In a 2x2x2 supercell, we expect some atoms near the center plane
        self.assertGreater(len(indices), 0)

if __name__ == '__main__':
    unittest.main()