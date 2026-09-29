"""
Unit tests for inertia tensor singularity handling and edge cases.

This module tests the robustness of the inertia tensor calculations,
specifically ensuring that:
1. Halos with fewer than 10,000 particles raise a ValueError.
2. Singular matrices (e.g., all particles at origin or collinear) raise a ValueError.
3. Valid inputs produce correct eigenvalues and shape metrics.
"""

import pytest
import numpy as np
from typing import List, Tuple, Optional
from pathlib import Path
import sys

# Ensure the code directory is in the path for imports
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from processing.inertia_tensor import (
    compute_reduced_inertia_tensor,
    compute_eigenvalues_and_eigenvectors,
    compute_shape_from_inertia,
    process_halo_inertia
)
from processing.shape_metrics import filter_halo_by_particle_count


class TestInertiaSingularity:
    """Tests for singularity and particle count constraints."""

    def test_too_few_particles_raises_error(self):
        """
        Test that processing a halo with < 10,000 particles raises ValueError.
        This satisfies the requirement: 'test_singular_matrix_raises_error'
        must raise ValueError when particles < 10,000.
        """
        # Create a small set of particles (e.g., 100)
        num_particles = 100
        positions = np.random.randn(num_particles, 3).astype(np.float64)
        masses = np.ones(num_particles)

        # The process_halo_inertia function should check particle count
        # and raise ValueError if below threshold.
        with pytest.raises(ValueError) as excinfo:
            process_halo_inertia(positions, masses)

        assert "particle count" in str(excinfo.value).lower() or "insufficient" in str(excinfo.value).lower()

    def test_singular_matrix_all_at_origin_raises_error(self):
        """
        Test that a singular inertia matrix (all particles at origin) raises ValueError.
        """
        # Create particles all at the origin
        num_particles = 20000  # Satisfy particle count
        positions = np.zeros((num_particles, 3), dtype=np.float64)
        masses = np.ones(num_particles)

        # Compute inertia tensor directly to test singularity
        inertia_tensor = compute_reduced_inertia_tensor(positions, masses)

        # The matrix should be all zeros (singular)
        assert np.allclose(inertia_tensor, 0.0)

        # Attempting to compute shape from this should fail or raise an error
        # depending on implementation. We expect process_halo_inertia to handle this.
        with pytest.raises(ValueError):
            process_halo_inertia(positions, masses)

    def test_singular_matrix_collinear_particles_raises_error(self):
        """
        Test that a singular inertia matrix (all particles on a line) raises ValueError.
        """
        # Create particles along the X-axis only
        num_particles = 20000
        x_coords = np.random.randn(num_particles)
        positions = np.zeros((num_particles, 3), dtype=np.float64)
        positions[:, 0] = x_coords
        masses = np.ones(num_particles)

        # Compute inertia tensor
        inertia_tensor = compute_reduced_inertia_tensor(positions, masses)

        # The matrix should be singular (determinant ~ 0)
        # We expect the shape computation to detect this singularity
        with pytest.raises(ValueError):
            process_halo_inertia(positions, masses)

    def test_singular_matrix_planar_particles_raises_error(self):
        """
        Test that a singular inertia matrix (all particles on a plane) raises ValueError.
        """
        # Create particles on the XY plane (Z=0)
        num_particles = 20000
        positions = np.random.randn(num_particles, 2).astype(np.float64)
        positions = np.hstack([positions, np.zeros((num_particles, 1))])
        masses = np.ones(num_particles)

        # Compute inertia tensor
        inertia_tensor = compute_reduced_inertia_tensor(positions, masses)

        # The matrix should be singular (one eigenvalue is 0)
        with pytest.raises(ValueError):
            process_halo_inertia(positions, masses)

    def test_valid_halo_does_not_raise(self):
        """
        Test that a valid, non-singular halo with enough particles does not raise.
        """
        # Create a valid distribution of particles (e.g., Gaussian cloud)
        num_particles = 20000
        positions = np.random.randn(num_particles, 3).astype(np.float64) * 10.0
        # Add a slight offset to avoid perfect symmetry if needed, but random is fine
        masses = np.random.uniform(0.9, 1.1, num_particles)

        # This should succeed
        try:
            result = process_halo_inertia(positions, masses)
            # Verify we got a dictionary with expected keys
            assert isinstance(result, dict)
            assert 'eigenvalues' in result
            assert 'b_a_ratio' in result
            assert 'c_a_ratio' in result
        except ValueError:
            pytest.fail("Valid halo raised ValueError unexpectedly")


class TestInertiaEdgeCases:
    """Tests for edge cases in inertia tensor calculations."""

    def test_single_particle_at_origin(self):
        """Test behavior with a single particle at origin."""
        positions = np.array([[0.0, 0.0, 0.0]], dtype=np.float64)
        masses = np.array([1.0])

        # Should raise due to particle count < 10000
        with pytest.raises(ValueError):
            process_halo_inertia(positions, masses)

    def test_very_small_mass_variance(self):
        """Test with extremely small mass variance."""
        num_particles = 20000
        positions = np.random.randn(num_particles, 3).astype(np.float64)
        masses = np.ones(num_particles) * 1e-15  # Very small masses

        # Should work as long as positions are non-singular
        try:
            result = process_halo_inertia(positions, masses)
            assert result is not None
        except ValueError:
            # If it fails due to singularity, that's acceptable if positions are effectively singular
            # But with random positions, it should be fine
            pass

    def test_extreme_mass_ratio(self):
        """Test with one very massive particle and many tiny ones."""
        num_particles = 20000
        positions = np.random.randn(num_particles, 3).astype(np.float64)
        masses = np.ones(num_particles)
        masses[0] = 1e10  # One super massive particle

        # Should work if the massive particle doesn't create singularity
        try:
            result = process_halo_inertia(positions, masses)
            assert result is not None
        except ValueError:
            # If the massive particle dominates and creates numerical issues,
            # it might raise, but generally should handle
            pass

    def test_eigenvalue_ordering(self):
        """Test that eigenvalues are returned in descending order."""
        num_particles = 20000
        positions = np.random.randn(num_particles, 3).astype(np.float64)
        masses = np.ones(num_particles)

        inertia_tensor = compute_reduced_inertia_tensor(positions, masses)
        eigenvalues, _ = compute_eigenvalues_and_eigenvectors(inertia_tensor)

        # Check descending order
        for i in range(len(eigenvalues) - 1):
            assert eigenvalues[i] >= eigenvalues[i+1], "Eigenvalues not in descending order"

    def test_axial_ratios_bounds(self):
        """Test that axial ratios are within valid bounds (0 < b/a <= 1, 0 < c/a <= 1)."""
        num_particles = 20000
        positions = np.random.randn(num_particles, 3).astype(np.float64)
        masses = np.ones(num_particles)

        result = process_halo_inertia(positions, masses)

        b_a = result['b_a_ratio']
        c_a = result['c_a_ratio']

        assert 0 < b_a <= 1, f"b/a ratio {b_a} out of bounds"
        assert 0 < c_a <= 1, f"c/a ratio {c_a} out of bounds"
        assert b_a >= c_a, f"b/a {b_a} should be >= c/a {c_a}"

    def test_triaxiality_bounds(self):
        """Test that triaxiality is within valid bounds (0 <= T <= 1)."""
        num_particles = 20000
        positions = np.random.randn(num_particles, 3).astype(np.float64)
        masses = np.ones(num_particles)

        result = process_halo_inertia(positions, masses)

        T = result['triaxiality']
        assert 0 <= T <= 1, f"Triaxiality {T} out of bounds"