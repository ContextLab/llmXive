"""
Unit tests for inertia tensor singularity handling.

This module tests the robustness of the inertia tensor calculations
when encountering singular or near-singular matrices, which can occur
with degenerate particle distributions (e.g., all particles on a line or plane).

Depends on T012 completion: The interface in code/processing/inertia_tensor.py
must exist before these tests can be run.
"""

import pytest
import numpy as np
from typing import List, Tuple, Optional
from pathlib import Path
import sys

# Add project root to path if needed
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from processing.inertia_tensor import (
    compute_reduced_inertia_tensor,
    compute_eigenvalues_and_eigenvectors,
    compute_shape_from_inertia,
    process_halo_inertia
)


class TestInertiaSingularity:
    """Tests for handling singular and near-singular inertia tensors."""
    
    def test_singular_tensor_all_particles_at_origin(self):
        """Test that a tensor with all particles at the origin (zero mass) is handled."""
        # Create positions where all particles are at the origin
        positions = np.array([
            [0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0]
        ], dtype=np.float64)
        
        masses = np.ones(5)  # Equal masses
        
        # This should not crash; it should return a singular matrix or handle gracefully
        inertia = compute_reduced_inertia_tensor(positions, masses)
        
        # The tensor should be all zeros (or very close)
        assert np.allclose(inertia, np.zeros((3, 3))), \
            "Tensor for particles at origin should be zero"
        
        # Eigenvalues should be zero
        eigenvalues, eigenvectors = compute_eigenvalues_and_eigenvectors(inertia)
        assert np.allclose(eigenvalues, np.zeros(3)), \
            "Eigenvalues for zero tensor should be zero"
    
    def test_singular_tensor_collinear_particles(self):
        """Test handling of particles arranged on a single line (rank-1 matrix)."""
        # Create positions along the x-axis only
        positions = np.array([
            [1.0, 0.0, 0.0],
            [2.0, 0.0, 0.0],
            [3.0, 0.0, 0.0],
            [4.0, 0.0, 0.0],
            [5.0, 0.0, 0.0]
        ], dtype=np.float64)
        
        masses = np.ones(5)
        
        inertia = compute_reduced_inertia_tensor(positions, masses)
        
        # The tensor should have rank 1 (only one non-zero eigenvalue)
        eigenvalues, eigenvectors = compute_eigenvalues_and_eigenvectors(inertia)
        
        # Sort eigenvalues in descending order
        eigenvalues_sorted = np.sort(eigenvalues)[::-1]
        
        # First eigenvalue should be non-zero, others should be near zero
        assert eigenvalues_sorted[0] > 1e-10, \
            "First eigenvalue should be non-zero for collinear particles"
        assert np.allclose(eigenvalues_sorted[1:], 0.0, atol=1e-10), \
            "Other eigenvalues should be near zero for collinear particles"
    
    def test_singular_tensor_coplanar_particles(self):
        """Test handling of particles arranged on a single plane (rank-2 matrix)."""
        # Create positions on the xy-plane (z=0)
        positions = np.array([
            [1.0, 1.0, 0.0],
            [2.0, 3.0, 0.0],
            [4.0, 2.0, 0.0],
            [5.0, 5.0, 0.0],
            [3.0, 4.0, 0.0]
        ], dtype=np.float64)
        
        masses = np.ones(5)
        
        inertia = compute_reduced_inertia_tensor(positions, masses)
        
        eigenvalues, eigenvectors = compute_eigenvalues_and_eigenvectors(inertia)
        
        # Sort eigenvalues in descending order
        eigenvalues_sorted = np.sort(eigenvalues)[::-1]
        
        # Two eigenvalues should be non-zero, one should be near zero
        assert eigenvalues_sorted[0] > 1e-10, \
            "First eigenvalue should be non-zero"
        assert eigenvalues_sorted[1] > 1e-10, \
            "Second eigenvalue should be non-zero"
        assert np.isclose(eigenvalues_sorted[2], 0.0, atol=1e-10), \
            "Third eigenvalue should be near zero for coplanar particles"
    
    def test_near_singular_tensor(self):
        """Test handling of nearly singular (ill-conditioned) matrices."""
        # Create positions that are nearly collinear but with tiny perturbations
        positions = np.array([
            [1.0, 0.0, 0.0],
            [2.0, 1e-10, 0.0],
            [3.0, 2e-10, 0.0],
            [4.0, 3e-10, 0.0],
            [5.0, 4e-10, 0.0]
        ], dtype=np.float64)
        
        masses = np.ones(5)
        
        # This should not raise an exception
        inertia = compute_reduced_inertia_tensor(positions, masses)
        eigenvalues, eigenvectors = compute_eigenvalues_and_eigenvectors(inertia)
        
        # Should complete without crashing
        assert eigenvalues is not None
        assert len(eigenvalues) == 3
        
        # Eigenvalues should be sorted in descending order by convention
        assert eigenvalues[0] >= eigenvalues[1] >= eigenvalues[2]
    
    def test_shape_computation_with_singular_tensor(self):
        """Test that shape metrics handle singular tensors gracefully."""
        # Create a singular tensor (all particles at origin)
        inertia = np.zeros((3, 3), dtype=np.float64)
        
        # This should not crash
        result = compute_shape_from_inertia(inertia)
        
        # Result should have expected keys
        assert 'axial_ratios' in result
        assert 'triaxiality' in result
        
        # For a singular tensor, axial ratios should be NaN or 0
        # (depending on implementation choice for division by zero)
        axial_ratios = result['axial_ratios']
        triaxiality = result['triaxiality']
        
        # The function should handle the edge case without raising
        # It may return NaN, 0, or some sentinel value
        assert not (np.isnan(triaxiality) and np.isnan(axial_ratios[0]) and 
                   np.isnan(axial_ratios[1])), \
            "At least some values should be defined even for singular tensors"
    
    def test_process_halo_inertia_with_singular_data(self):
        """Test the full pipeline function with singular input data."""
        # Create a minimal halo with singular particle distribution
        halo_data = {
            'positions': np.array([
                [0.0, 0.0, 0.0],
                [0.0, 0.0, 0.0],
                [0.0, 0.0, 0.0]
            ], dtype=np.float64),
            'masses': np.ones(3),
            'halo_id': 999,
            'particle_count': 3
        }
        
        # This should not crash
        result = process_halo_inertia(halo_data)
        
        # Result should contain expected fields
        assert 'halo_id' in result
        assert 'inertia_tensor' in result
        assert 'eigenvalues' in result
        assert 'axial_ratios' in result
        assert 'triaxiality' in result
    
    def test_eigenvalue_sorting(self):
        """Test that eigenvalues are consistently sorted."""
        # Create a known tensor with specific eigenvalues
        # Diagonal matrix with eigenvalues 3, 1, 2 (unsorted)
        inertia = np.diag([3.0, 1.0, 2.0])
        
        eigenvalues, eigenvectors = compute_eigenvalues_and_eigenvectors(inertia)
        
        # Eigenvalues should be sorted in descending order
        assert eigenvalues[0] >= eigenvalues[1] >= eigenvalues[2], \
            "Eigenvalues should be sorted in descending order"
        
        # Values should match (approximately)
        assert np.isclose(eigenvalues[0], 3.0)
        assert np.isclose(eigenvalues[1], 2.0)
        assert np.isclose(eigenvalues[2], 1.0)
    
    def test_positive_semidefinite_property(self):
        """Test that the inertia tensor is always positive semidefinite."""
        # Generate random positions and masses
        np.random.seed(42)  # For reproducibility
        positions = np.random.randn(100, 3) * 10.0
        masses = np.abs(np.random.randn(100)) + 0.1  # Positive masses
        
        inertia = compute_reduced_inertia_tensor(positions, masses)
        eigenvalues, _ = compute_eigenvalues_and_eigenvectors(inertia)
        
        # All eigenvalues should be non-negative
        assert np.all(eigenvalues >= -1e-10), \
            "Inertia tensor eigenvalues should be non-negative (positive semidefinite)"
    
    def test_ill_conditioned_matrix_handling(self):
        """Test handling of matrices with very high condition numbers."""
        # Create a matrix with very disparate eigenvalues
        # This simulates a highly elongated halo
        positions = np.array([
            [1000.0, 0.0, 0.0],
            [2000.0, 0.0, 0.0],
            [3000.0, 0.0, 0.0],
            [4000.0, 0.0, 0.0],
            [5000.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 2.0, 0.0],
            [0.0, 1.0, 0.5],
            [0.0, 1.5, 0.3],
            [0.0, 1.2, 0.4]
        ], dtype=np.float64)
        
        masses = np.ones(10)
        
        # Should not raise an exception
        inertia = compute_reduced_inertia_tensor(positions, masses)
        eigenvalues, eigenvectors = compute_eigenvalues_and_eigenvectors(inertia)
        
        # Should complete successfully
        assert len(eigenvalues) == 3
        assert eigenvalues[0] > eigenvalues[1] > eigenvalues[2]
        
        # The ratio of largest to smallest eigenvalue can be very large
        # but should be finite
        assert np.isfinite(eigenvalues[0] / eigenvalues[2]) or \
               (eigenvalues[2] == 0 and eigenvalues[0] > 0)


class TestInertiaEdgeCases:
    """Additional edge case tests for inertia tensor computation."""
    
    def test_single_particle(self):
        """Test with a single particle (degenerate case)."""
        positions = np.array([[1.0, 2.0, 3.0]], dtype=np.float64)
        masses = np.array([1.0])
        
        inertia = compute_reduced_inertia_tensor(positions, masses)
        
        # Single particle at position r relative to center of mass (which is the particle itself)
        # should result in zero tensor
        assert np.allclose(inertia, np.zeros((3, 3)))
    
    def test_two_particles(self):
        """Test with two particles."""
        positions = np.array([
            [-1.0, 0.0, 0.0],
            [1.0, 0.0, 0.0]
        ], dtype=np.float64)
        masses = np.array([1.0, 1.0])
        
        inertia = compute_reduced_inertia_tensor(positions, masses)
        
        # Center of mass is at origin
        # Tensor should have non-zero component only in x-direction (actually zero for reduced inertia)
        # For reduced inertia: I_ij = sum(m * x_i * x_j) / sum(m) - center_of_mass terms
        # With COM at origin, this simplifies
        eigenvalues, _ = compute_eigenvalues_and_eigenvectors(inertia)
        
        # Should not crash and should have valid eigenvalues
        assert len(eigenvalues) == 3
        assert np.all(eigenvalues >= -1e-10)
    
    def test_very_small_masses(self):
        """Test with very small mass values."""
        positions = np.array([
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0]
        ], dtype=np.float64)
        masses = np.array([1e-15, 1e-15, 1e-15])
        
        # Should not crash due to underflow
        inertia = compute_reduced_inertia_tensor(positions, masses)
        eigenvalues, _ = compute_eigenvalues_and_eigenvectors(inertia)
        
        assert len(eigenvalues) == 3
        assert np.all(np.isfinite(eigenvalues))
    
    def test_very_large_positions(self):
        """Test with very large position values."""
        positions = np.array([
            [1e10, 0.0, 0.0],
            [0.0, 1e10, 0.0],
            [0.0, 0.0, 1e10]
        ], dtype=np.float64)
        masses = np.array([1.0, 1.0, 1.0])
        
        # Should not crash due to overflow
        inertia = compute_reduced_inertia_tensor(positions, masses)
        eigenvalues, _ = compute_eigenvalues_and_eigenvectors(inertia)
        
        assert len(eigenvalues) == 3
        assert np.all(np.isfinite(eigenvalues))