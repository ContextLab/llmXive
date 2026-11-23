"""
Unit tests for sparsity density calculation and mask generation.

This module verifies the correctness of sparsity-related utilities used
in the sensitivity analysis of random matrix perturbations.

Tests cover:
- Sparsity density calculation (actual vs. target)
- Binary mask generation for various sparsity patterns
- Rank preservation under sparsity masking
- Edge cases (zero density, full density)
"""

import numpy as np
import pytest
from scipy import sparse
from pathlib import Path
import sys

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from generators.perturbation import create_perturbation
from utils.config import get_sparsity_density


class TestSparsityDensityCalculation:
    """Tests for sparsity density calculation functions."""
    
    def test_density_calculation_empty_matrix(self):
        """Test density calculation on an all-zero matrix."""
        n = 100
        matrix = np.zeros((n, n))
        density = np.count_nonzero(matrix) / (n * n)
        assert density == 0.0
        
    def test_density_calculation_full_matrix(self):
        """Test density calculation on a full matrix."""
        n = 100
        matrix = np.ones((n, n))
        density = np.count_nonzero(matrix) / (n * n)
        assert density == 1.0
        
    def test_density_calculation_half_full(self):
        """Test density calculation on a half-full matrix."""
        n = 100
        matrix = np.zeros((n, n))
        matrix[:n//2, :] = 1.0
        density = np.count_nonzero(matrix) / (n * n)
        assert abs(density - 0.5) < 1e-10
        
    def test_sparse_matrix_density(self):
        """Test density calculation on a sparse matrix."""
        n = 1000
        # Create a sparse matrix with known density
        nnz = 100
        rows = np.random.choice(n, nnz, replace=False)
        cols = np.random.choice(n, nnz, replace=False)
        data = np.random.randn(nnz)
        mat = sparse.csr_matrix((data, (rows, cols)), shape=(n, n))
        
        actual_density = mat.nnz / (n * n)
        expected_density = nnz / (n * n)
        assert abs(actual_density - expected_density) < 1e-10
        
class TestMaskGeneration:
    """Tests for binary mask generation with sparsity constraints."""
    
    def test_mask_generation_target_density(self):
        """Test that generated mask achieves target sparsity density."""
        n = 500
        target_density = 0.1
        
        # Generate a random mask
        mask = np.random.random((n, n))
        threshold = np.percentile(mask, 100 * (1 - target_density))
        binary_mask = (mask >= threshold).astype(float)
        
        actual_density = np.count_nonzero(binary_mask) / (n * n)
        # Allow small tolerance due to percentile rounding
        assert abs(actual_density - target_density) < 0.01
        
    def test_mask_generation_zero_density(self):
        """Test mask generation with zero target density."""
        n = 100
        target_density = 0.0
        
        mask = np.random.random((n, n))
        threshold = np.percentile(mask, 100 * (1 - target_density))
        binary_mask = (mask >= threshold).astype(float)
        
        actual_density = np.count_nonzero(binary_mask) / (n * n)
        assert actual_density == 0.0
        
    def test_mask_generation_full_density(self):
        """Test mask generation with full target density."""
        n = 100
        target_density = 1.0
        
        mask = np.random.random((n, n))
        threshold = np.percentile(mask, 100 * (1 - target_density))
        binary_mask = (mask >= threshold).astype(float)
        
        actual_density = np.count_nonzero(binary_mask) / (n * n)
        assert actual_density == 1.0
        
    def test_mask_preserves_rank_structure(self):
        """Test that masking preserves the rank structure of perturbations."""
        n = 200
        rank = 3
        target_density = 0.2
        
        # Create a rank-k perturbation (diagonal)
        perturbation = np.zeros((n, n))
        for i in range(rank):
            perturbation[i, i] = 2.5  # θ = 2.5
        
        # Generate sparse mask
        mask = np.random.random((n, n))
        threshold = np.percentile(mask, 100 * (1 - target_density))
        binary_mask = (mask >= threshold).astype(float)
        
        # Apply mask
        masked_perturbation = perturbation * binary_mask
        
        # Check that at least some of the rank structure is preserved
        # (not all non-zero elements should be zeroed out)
        original_nnz = np.count_nonzero(perturbation)
        masked_nnz = np.count_nonzero(masked_perturbation)
        
        # With 20% density, we expect roughly 20% of elements to remain
        expected_ratio = target_density
        actual_ratio = masked_nnz / original_nnz if original_nnz > 0 else 0
        
        # Allow some variance due to randomness
        assert actual_ratio > 0.05  # At least some structure preserved
        
class TestPerturbationWithSparsity:
    """Tests for perturbation generation with sparsity constraints."""
    
    def test_create_perturbation_with_sparsity(self):
        """Test that create_perturbation respects sparsity density."""
        n = 300
        rank = 2
        theta = 2.5
        target_density = 0.15
        
        # Create perturbation with sparsity
        perturbation = create_perturbation(
            n=n,
            rank=rank,
            theta=theta,
            sparsity_density=target_density,
            pattern='diagonal'
        )
        
        # Calculate actual density
        if isinstance(perturbation, sparse.spmatrix):
            actual_density = perturbation.nnz / (n * n)
        else:
            actual_density = np.count_nonzero(perturbation) / (n * n)
        
        # Allow tolerance for random variation
        assert abs(actual_density - target_density) < 0.02
        
    def test_create_perturbation_dense_vs_sparse(self):
        """Test that dense and sparse perturbations have different structures."""
        n = 200
        rank = 2
        theta = 2.5
        
        # Dense perturbation
        dense_pert = create_perturbation(
            n=n,
            rank=rank,
            theta=theta,
            sparsity_density=1.0,
            pattern='diagonal'
        )
        
        # Sparse perturbation
        sparse_pert = create_perturbation(
            n=n,
            rank=rank,
            theta=theta,
            sparsity_density=0.1,
            pattern='diagonal'
        )
        
        dense_nnz = np.count_nonzero(dense_pert)
        sparse_nnz = np.count_nonzero(sparse_pert)
        
        assert sparse_nnz < dense_nnz
        
    def test_create_perturbation_block_sparse(self):
        """Test block-sparse perturbation generation."""
        n = 400
        rank = 4
        theta = 2.5
        target_density = 0.2
        
        perturbation = create_perturbation(
            n=n,
            rank=rank,
            theta=theta,
            sparsity_density=target_density,
            pattern='block_sparse',
            block_size=10
        )
        
        actual_density = np.count_nonzero(perturbation) / (n * n)
        assert abs(actual_density - target_density) < 0.02
        
    def test_create_perturbation_random_sparse(self):
        """Test random-sparse perturbation generation."""
        n = 300
        rank = 3
        theta = 2.5
        target_density = 0.25
        
        perturbation = create_perturbation(
            n=n,
            rank=rank,
            theta=theta,
            sparsity_density=target_density,
            pattern='random_sparse'
        )
        
        actual_density = np.count_nonzero(perturbation) / (n * n)
        assert abs(actual_density - target_density) < 0.02
        
class TestEdgeCases:
    """Tests for edge cases in sparsity handling."""
    
    def test_very_small_matrix(self):
        """Test sparsity with very small matrix."""
        n = 10
        target_density = 0.3
        
        perturbation = create_perturbation(
            n=n,
            rank=1,
            theta=2.5,
            sparsity_density=target_density,
            pattern='diagonal'
        )
        
        actual_density = np.count_nonzero(perturbation) / (n * n)
        # Small matrices have coarse density steps
        assert actual_density <= target_density + 0.1
        
    def test_very_high_rank(self):
        """Test sparsity with rank approaching matrix size."""
        n = 100
        rank = 50
        target_density = 0.1
        
        perturbation = create_perturbation(
            n=n,
            rank=rank,
            theta=2.5,
            sparsity_density=target_density,
            pattern='diagonal'
        )
        
        actual_density = np.count_nonzero(perturbation) / (n * n)
        assert abs(actual_density - target_density) < 0.02
        
    def test_zero_rank_perturbation(self):
        """Test perturbation with rank=0 (unperturbed)."""
        n = 100
        
        perturbation = create_perturbation(
            n=n,
            rank=0,
            theta=0.0,
            sparsity_density=0.1,
            pattern='diagonal'
        )
        
        assert np.allclose(perturbation, 0)
        
class TestReproducibility:
    """Tests for reproducibility of sparsity operations."""
    
    def test_seed_reproducibility(self):
        """Test that same seed produces same sparsity pattern."""
        n = 200
        rank = 2
        theta = 2.5
        target_density = 0.2
        seed = 42
        
        perturbation1 = create_perturbation(
            n=n,
            rank=rank,
            theta=theta,
            sparsity_density=target_density,
            pattern='diagonal',
            seed=seed
        )
        
        perturbation2 = create_perturbation(
            n=n,
            rank=rank,
            theta=theta,
            sparsity_density=target_density,
            pattern='diagonal',
            seed=seed
        )
        
        assert np.array_equal(perturbation1, perturbation2)
        
    def test_different_seed_different_pattern(self):
        """Test that different seeds produce different sparsity patterns."""
        n = 200
        rank = 2
        theta = 2.5
        target_density = 0.2
        
        perturbation1 = create_perturbation(
            n=n,
            rank=rank,
            theta=theta,
            sparsity_density=target_density,
            pattern='diagonal',
            seed=42
        )
        
        perturbation2 = create_perturbation(
            n=n,
            rank=rank,
            theta=theta,
            sparsity_density=target_density,
            pattern='diagonal',
            seed=123
        )
        
        assert not np.array_equal(perturbation1, perturbation2)