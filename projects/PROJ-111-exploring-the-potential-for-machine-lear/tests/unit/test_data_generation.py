"""
Unit tests for data_generation.py.

Tests verify:
- Correct initialization of spins (norm = 1).
- Correct energy calculation (shape and sign).
- Simulation runs without error for a small step count.
"""
import os
import sys
import unittest
import numpy as np
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data_generation import (
    initialize_spins_heisenberg,
    initialize_spins_xy,
    energy_heisenberg,
    energy_xy,
    metropolis_step_heisenberg,
    metropolis_step_xy,
    COUPLING_J1
)

class TestDataGeneration(unittest.TestCase):

    def test_initialize_heisenberg_shape(self):
        L = 4
        spins = initialize_spins_heisenberg(L, seed=42)
        self.assertEqual(spins.shape, (L * L, 3))

    def test_initialize_heisenberg_normalized(self):
        L = 4
        spins = initialize_spins_heisenberg(L, seed=42)
        norms = np.linalg.norm(spins, axis=1)
        np.testing.assert_array_almost_equal(norms, np.ones(L * L), decimal=5)

    def test_initialize_xy_shape(self):
        L = 4
        spins = initialize_spins_xy(L, seed=42)
        self.assertEqual(spins.shape, (L * L, 2))

    def test_initialize_xy_normalized(self):
        L = 4
        spins = initialize_spins_xy(L, seed=42)
        norms = np.linalg.norm(spins, axis=1)
        np.testing.assert_array_almost_equal(norms, np.ones(L * L), decimal=5)

    def test_energy_heisenberg_shape(self):
        L = 4
        spins = initialize_spins_heisenberg(L, seed=42)
        energy = energy_heisenberg(spins, L, J1=1.0, J2=0.0)
        self.assertIsInstance(energy, float)

    def test_energy_xy_shape(self):
        L = 4
        spins = initialize_spins_xy(L, seed=42)
        energy = energy_xy(spins, L, J1=1.0, J2=0.0)
        self.assertIsInstance(energy, float)

    def test_metropolis_step_heisenberg_preserves_norm(self):
        L = 4
        spins = initialize_spins_heisenberg(L, seed=42)
        rng = np.random.default_rng(123)
        new_spins = metropolis_step_heisenberg(spins, L, 1.0, 0.0, 1.0, rng)
        norms = np.linalg.norm(new_spins, axis=1)
        np.testing.assert_array_almost_equal(norms, np.ones(L * L), decimal=5)

    def test_metropolis_step_xy_preserves_norm(self):
        L = 4
        spins = initialize_spins_xy(L, seed=42)
        rng = np.random.default_rng(123)
        new_spins = metropolis_step_xy(spins, L, 1.0, 0.0, 1.0, rng)
        norms = np.linalg.norm(new_spins, axis=1)
        np.testing.assert_array_almost_equal(norms, np.ones(L * L), decimal=5)

    def test_energy_comparison_heisenberg(self):
        # Test that energy is lower for aligned spins (ferromagnetic)
        L = 4
        # All aligned
        aligned = np.ones((L*L, 3))
        aligned = aligned / np.linalg.norm(aligned[0]) # Normalize one, then broadcast logic? No, normalize all.
        aligned = np.tile(np.array([1.0, 0.0, 0.0]), (L*L, 1))
        
        # Random
        random_spins = initialize_spins_heisenberg(L, seed=42)
        
        E_aligned = energy_heisenberg(aligned, L, J1=1.0, J2=0.0)
        E_random = energy_heisenberg(random_spins, L, J1=1.0, J2=0.0)
        
        # For ferromagnetic coupling (J1=1), aligned state should have lower (more negative) energy
        self.assertLess(E_aligned, E_random)

    def test_energy_comparison_xy(self):
        L = 4
        aligned = np.tile(np.array([1.0, 0.0]), (L*L, 1))
        random_spins = initialize_spins_xy(L, seed=42)
        
        E_aligned = energy_xy(aligned, L, J1=1.0, J2=0.0)
        E_random = energy_xy(random_spins, L, J1=1.0, J2=0.0)
        
        self.assertLess(E_aligned, E_random)

if __name__ == "__main__":
    unittest.main()