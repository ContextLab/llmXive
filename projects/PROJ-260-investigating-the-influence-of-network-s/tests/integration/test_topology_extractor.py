import unittest
import os
import numpy as np
from src.services.topology_extractor import extract_topology
from ase import Atoms
from ase.build import fcc111

class TestTopologyExtractor(unittest.TestCase):
    def test_valid_trajectory(self):
        # Create a simple test trajectory
        atoms = fcc111('Si', size=(1, 1, 1))
        trajectory_file = "test_trajectory.xyz"
        atoms.write(trajectory_file)

        coordination_numbers, bond_angle_variances = extract_topology(trajectory_file)

        self.assertIsNotNone(coordination_numbers)
        self.assertIsNotNone(bond_angle_variances)

        # Check if the results are reasonable (e.g., coordination numbers are within a certain range)
        self.assertTrue(np.all(coordination_numbers >= 0))
        self.assertTrue(np.all(bond_angle_variances >= 0))

        os.remove(trajectory_file)

    def test_invalid_trajectory(self):
        # Test with an invalid trajectory file
        with self.assertRaises(Exception):
            extract_topology("nonexistent_file.xyz")