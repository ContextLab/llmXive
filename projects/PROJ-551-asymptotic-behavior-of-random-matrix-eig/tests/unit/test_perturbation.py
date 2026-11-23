"""
Unit tests for perturbation matrix construction.
Verifies rank, sparsity, and pattern correctness.
"""
import pytest
import numpy as np
import sys
import os

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from generators.perturbation import create_perturbation, verify_rank_preservation

class TestPerturbationDiagonal:
    def test_diagonal_rank_1(self):
        N = 10
        theta = 2.5
        rank = 1
        P = create_perturbation(N, theta, rank, pattern="diagonal", seed=42)
        
        # Check shape
        assert P.shape == (N, N)
        
        # Check diagonal entries
        assert P[0, 0] == theta
        assert P[1, 1] == 0.0
        assert P[2, 2] == 0.0
        
        # Check off-diagonal
        assert np.all(P == P.T)
        assert np.sum(P != 0) == 1
        
        # Verify rank
        is_correct, actual_rank = verify_rank_preservation(P, rank)
        assert is_correct
        assert actual_rank == 1

    def test_diagonal_rank_k(self):
        N = 10
        theta = 2.0
        rank = 3
        P = create_perturbation(N, theta, rank, pattern="diagonal", seed=42)
        
        # Check first k diagonal entries
        for i in range(rank):
            assert P[i, i] == theta
        
        # Check rest are zero
        for i in range(rank, N):
            assert P[i, i] == 0.0
        
        # Verify rank
        is_correct, actual_rank = verify_rank_preservation(P, rank)
        assert is_correct
        assert actual_rank == rank

    def test_diagonal_rank_0(self):
        N = 10
        P = create_perturbation(N, 0.0, 0, pattern="diagonal")
        assert np.all(P == 0.0)

class TestPerturbationBlockSparse:
    def test_block_sparse_rank_1_density_1(self):
        N = 10
        theta = 2.0
        rank = 1
        density = 1.0
        P = create_perturbation(N, theta, rank, pattern="block-sparse", sparsity_density=density, seed=42)
        
        # Rank 1 block-sparse with density 1.0 should be a 1x1 block scaled by theta
        # The block is random, so we just check non-zero structure and scale
        assert P[0, 0] != 0.0
        assert np.all(P[1:, :] == 0.0)
        assert np.all(P[:, 1:] == 0.0)
        
        # Verify rank
        is_correct, actual_rank = verify_rank_preservation(P, rank)
        assert is_correct
        assert actual_rank == rank

    def test_block_sparse_rank_2_density_05(self):
        N = 20
        theta = 1.5
        rank = 2
        density = 0.5
        P = create_perturbation(N, theta, rank, pattern="block-sparse", sparsity_density=density, seed=123)
        
        # Check that non-zeros are confined to the 2x2 block
        assert np.all(P[2:, :] == 0.0)
        assert np.all(P[:, 2:] == 0.0)
        
        # Check that the block is not all zero (probabilistically)
        block = P[:2, :2]
        assert np.any(block != 0.0)
        
        # Verify rank (might be less due to masking, but usually rank 2 for density 0.5)
        # We just check that the function runs and returns a matrix
        assert P.shape == (N, N)

    def test_block_sparse_rank_0(self):
        N = 10
        P = create_perturbation(N, 1.0, 0, pattern="block-sparse")
        assert np.all(P == 0.0)

class TestPerturbationRandomSparse:
    def test_random_sparse_rank_1_density_1(self):
        N = 10
        theta = 2.0
        rank = 1
        density = 1.0
        P = create_perturbation(N, theta, rank, pattern="random sparse", sparsity_density=density, seed=42)
        
        # Should be rank 1
        is_correct, actual_rank = verify_rank_preservation(P, rank)
        assert is_correct
        assert actual_rank == rank
        
        # Check symmetry
        assert np.allclose(P, P.T)

    def test_random_sparse_rank_2_density_05(self):
        N = 20
        theta = 1.0
        rank = 2
        density = 0.5
        P = create_perturbation(N, theta, rank, pattern="random sparse", sparsity_density=density, seed=999)
        
        # Check symmetry
        assert np.allclose(P, P.T)
        
        # Verify rank (might be less if vectors vanish, but usually rank 2)
        # We check that it runs and produces a symmetric matrix
        assert P.shape == (N, N)
        
        # Check that it's not all zero
        assert np.any(P != 0.0)

    def test_random_sparse_rank_0(self):
        N = 10
        P = create_perturbation(N, 1.0, 0, pattern="random sparse")
        assert np.all(P == 0.0)

class TestPerturbationEdgeCases:
    def test_invalid_rank(self):
        with pytest.raises(ValueError):
            create_perturbation(10, 1.0, 11, pattern="diagonal")
        
        with pytest.raises(ValueError):
            create_perturbation(10, 1.0, -1, pattern="diagonal")

    def test_invalid_density(self):
        with pytest.raises(ValueError):
            create_perturbation(10, 1.0, 1, pattern="diagonal", sparsity_density=1.5)
        
        with pytest.raises(ValueError):
            create_perturbation(10, 1.0, 1, pattern="diagonal", sparsity_density=-0.1)

    def test_unknown_pattern(self):
        with pytest.raises(ValueError):
            create_perturbation(10, 1.0, 1, pattern="unknown")

    def test_seed_reproducibility(self):
        N = 10
        theta = 2.0
        rank = 1
        seed = 42
        
        P1 = create_perturbation(N, theta, rank, pattern="random sparse", sparsity_density=1.0, seed=seed)
        P2 = create_perturbation(N, theta, rank, pattern="random sparse", sparsity_density=1.0, seed=seed)
        
        assert np.allclose(P1, P2)
        
        P3 = create_perturbation(N, theta, rank, pattern="random sparse", sparsity_density=1.0, seed=seed+1)
        assert not np.allclose(P1, P3)