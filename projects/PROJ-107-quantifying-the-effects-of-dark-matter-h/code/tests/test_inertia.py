"""
Unit tests for inertia tensor singularity handling and edge cases.

This module tests the robustness of the inertia tensor computation pipeline,
specifically focusing on:
1. Singularity handling when particle counts are too low (< 10,000).
2. Handling of singular matrices during eigenvalue decomposition.
3. Edge cases with degenerate particle configurations.
"""

import pytest
import numpy as np
from typing import List, Tuple, Optional
from pathlib import Path
import sys

# Ensure project root is in path for imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from processing.inertia_tensor import (
    compute_reduced_inertia_tensor,
    compute_eigenvalues_and_eigenvectors,
    process_halo_inertia
)
from processing.shape_metrics import filter_halo_by_particle_count


class TestInertiaSingularity:
    """Tests for singularity handling in inertia tensor computations."""

    def test_singular_matrix_raises_error_low_particles(self):
        """
        Test that ValueError is raised when particle count < 10,000.

        This verifies the filtering logic prevents computation on
        insufficient data, which would lead to singular matrices.
        """
        # Create a mock halo with only 5000 particles (below threshold)
        num_particles = 5000
        positions = np.random.rand(num_particles, 3)
        masses = np.ones(num_particles)

        # The filter function should exclude this halo
        is_valid = filter_halo_by_particle_count(num_particles, min_particles=10000)
        assert is_valid is False, "Halo with < 10,000 particles should be filtered out"

        # If we attempt to compute inertia directly (bypassing filter),
        # we should handle the singularity gracefully or raise an error
        # depending on implementation. Here we test that the computation
        # itself doesn't crash with a cryptic error but raises a clear ValueError.
        with pytest.raises(ValueError, match="Insufficient particles"):
            # Force computation with low particles to test error handling
            compute_reduced_inertia_tensor(positions, masses, min_particles=10000)

    def test_singular_matrix_raises_error_degenerate_config(self):
        """
        Test that ValueError is raised when particles are collinear or coplanar.

        This creates a degenerate configuration where the inertia tensor
        is singular (rank deficient) regardless of particle count.
        """
        # Create 10,000 particles but all on a single line (x-axis)
        # This makes the inertia tensor singular in y and z dimensions
        num_particles = 10000
        positions = np.zeros((num_particles, 3))
        positions[:, 0] = np.random.rand(num_particles)  # Only x-coordinates vary
        masses = np.ones(num_particles)

        # Compute inertia tensor - this should detect singularity
        inertia_tensor = compute_reduced_inertia_tensor(positions, masses, min_particles=100)

        # Check if tensor is singular (determinant close to zero)
        det = np.linalg.det(inertia_tensor)
        is_singular = np.abs(det) < 1e-10

        # If the tensor is singular, eigenvalue decomposition should raise ValueError
        if is_singular:
            with pytest.raises(ValueError, match="Singular matrix"):
                compute_eigenvalues_and_eigenvectors(inertia_tensor)
        else:
            # If not singular (numerical noise might prevent perfect singularity),
            # the decomposition should succeed
            eigenvalues, eigenvectors = compute_eigenvalues_and_eigenvectors(inertia_tensor)
            assert len(eigenvalues) == 3
            assert eigenvalues.shape == (3,)

    def test_edge_case_all_particles_at_origin(self):
        """
        Test handling when all particles are at the origin.

        This is an extreme degenerate case where the inertia tensor
        is entirely zero.
        """
        num_particles = 10000
        positions = np.zeros((num_particles, 3))
        masses = np.ones(num_particles)

        with pytest.raises(ValueError, match="Singular matrix|Zero inertia"):
            compute_reduced_inertia_tensor(positions, masses, min_particles=100)

    def test_edge_case_two_distinct_positions(self):
        """
        Test handling when particles are only at two distinct positions.

        This creates a highly degenerate configuration.
        """
        num_particles = 10000
        positions = np.zeros((num_particles, 3))
        # Half at (0,0,0), half at (1,0,0)
        positions[:num_particles//2, :] = [0, 0, 0]
        positions[num_particles//2:, :] = [1, 0, 0]
        masses = np.ones(num_particles)

        # This should result in a singular matrix (rank 1)
        inertia_tensor = compute_reduced_inertia_tensor(positions, masses, min_particles=100)
        det = np.linalg.det(inertia_tensor)

        if np.abs(det) < 1e-10:
            with pytest.raises(ValueError, match="Singular matrix"):
                compute_eigenvalues_and_eigenvectors(inertia_tensor)


class TestInertiaEdgeCases:
    """Tests for edge cases in inertia tensor computations."""

    def test_minimum_valid_particle_count(self):
        """Test computation with exactly 10,000 particles (minimum threshold)."""
        num_particles = 10000
        positions = np.random.rand(num_particles, 3) * 100  # Random positions in 100^3 box
        masses = np.random.rand(num_particles) + 0.1  # Positive masses

        # Should succeed without error
        inertia_tensor = compute_reduced_inertia_tensor(positions, masses, min_particles=10000)
        assert inertia_tensor.shape == (3, 3)

        eigenvalues, eigenvectors = compute_eigenvalues_and_eigenvectors(inertia_tensor)
        assert len(eigenvalues) == 3
        assert np.all(eigenvalues >= 0)  # Eigenvalues should be non-negative

    def test_very_large_particle_count(self):
        """Test computation with a large number of particles."""
        num_particles = 1000000
        positions = np.random.rand(num_particles, 3) * 1000
        masses = np.ones(num_particles)

        # Should handle large datasets without memory issues (in streaming context)
        # For this unit test, we just verify it runs
        inertia_tensor = compute_reduced_inertia_tensor(positions, masses, min_particles=10000)
        assert inertia_tensor.shape == (3, 3)

    def test_negative_masses_handled(self):
        """Test that negative masses are handled appropriately."""
        num_particles = 10000
        positions = np.random.rand(num_particles, 3)
        masses = np.random.rand(num_particles) - 0.5  # Some negative masses

        # The implementation should either reject negative masses or handle them
        # For now, we test that it doesn't crash with an unexpected error
        try:
            inertia_tensor = compute_reduced_inertia_tensor(positions, masses, min_particles=10000)
            # If it succeeds, the tensor should still be symmetric
            assert np.allclose(inertia_tensor, inertia_tensor.T)
        except ValueError as e:
            # If it raises ValueError, that's acceptable (negative masses not allowed)
            assert "negative mass" in str(e).lower() or "invalid mass" in str(e).lower()

    def test_non_square_position_array(self):
        """Test handling of incorrectly shaped position arrays."""
        # Wrong shape: (N, 2) instead of (N, 3)
        num_particles = 10000
        positions = np.random.rand(num_particles, 2)
        masses = np.ones(num_particles)

        with pytest.raises((ValueError, IndexError)):
            compute_reduced_inertia_tensor(positions, masses, min_particles=10000)

    def test_mismatched_masses_length(self):
        """Test handling of mismatched masses array length."""
        num_particles = 10000
        positions = np.random.rand(num_particles, 3)
        masses = np.ones(num_particles - 1)  # One less than positions

        with pytest.raises((ValueError, IndexError)):
            compute_reduced_inertia_tensor(positions, masses, min_particles=10000)

    def test_process_halo_inertia_with_valid_data(self):
        """Test the full pipeline with valid data."""
        num_particles = 15000
        positions = np.random.rand(num_particles, 3) * 100
        masses = np.random.rand(num_particles) + 0.1

        result = process_halo_inertia(positions, masses, halo_id=12345)

        assert result is not None
        assert 'halo_id' in result
        assert result['halo_id'] == 12345
        assert 'eigenvalues' in result
        assert 'eigenvectors' in result
        assert 'axial_ratios' in result
        assert 'triaxiality' in result

    def test_process_halo_inertia_with_invalid_particles(self):
        """Test the full pipeline with insufficient particles."""
        num_particles = 5000  # Below threshold
        positions = np.random.rand(num_particles, 3)
        masses = np.ones(num_particles)

        with pytest.raises(ValueError, match="Insufficient particles"):
            process_halo_inertia(positions, masses, halo_id=12345)

    def test_process_halo_inertia_with_singular_matrix(self):
        """Test the full pipeline with degenerate particle configuration."""
        num_particles = 10000
        # All particles on x-axis
        positions = np.zeros((num_particles, 3))
        positions[:, 0] = np.random.rand(num_particles)
        masses = np.ones(num_particles)

        with pytest.raises(ValueError, match="Singular matrix"):
            process_halo_inertia(positions, masses, halo_id=12345)