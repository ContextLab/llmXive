"""
Unit tests for refactored FTLE module.
Tests the refactored FTLE functions added in T038.
"""
import pytest
import numpy as np
from pathlib import Path
import tempfile
import json

from analysis.refactored_ftle import (
    compute_jacobian, propagate_tangent_vectors, orthonormalize,
    compute_ftle_single_trajectory, run_sliding_window_sweep,
    compute_ftle_batch, FTLEResult
)


class TestComputeJacobian:
    """Tests for Jacobian computation."""
    
    def test_single_oscillator_shape(self):
        state = np.array([1.0, 1.0, 1.0])
        jacobian = compute_jacobian(state, N=1)
        assert jacobian.shape == (3, 3)
    
    def test_multiple_oscillators_shape(self):
        N = 5
        state = np.random.randn(3 * N)
        jacobian = compute_jacobian(state, N=N)
        assert jacobian.shape == (3 * N, 3 * N)
    
    def test_jacobian_values(self):
        # Test with known state
        state = np.array([1.0, 2.0, 3.0] * 5)
        jacobian = compute_jacobian(state, N=5)
        
        # Check that Jacobian is not all zeros
        assert np.any(jacobian != 0)
        
        # Check diagonal structure for first oscillator
        assert jacobian[0, 0] == -10.0  # -sigma_param
        assert jacobian[0, 1] == 10.0   # sigma_param


class TestPropagateTangentVectors:
    """Tests for tangent vector propagation."""
    
    def test_propagation_updates_matrix(self):
        jacobian = np.eye(3) * 0.1
        tangent_matrix = np.eye(3)
        dt = 0.01
        
        result = propagate_tangent_vectors(jacobian, tangent_matrix, dt)
        
        # Result should be different from initial
        assert not np.allclose(result, tangent_matrix)
        
        # Should be close for small dt
        expected = tangent_matrix + dt @ (jacobian @ tangent_matrix)
        assert np.allclose(result, expected)
    
    def test_zero_jacobian(self):
        jacobian = np.zeros((3, 3))
        tangent_matrix = np.eye(3)
        dt = 0.01
        
        result = propagate_tangent_vectors(jacobian, tangent_matrix, dt)
        assert np.allclose(result, tangent_matrix)


class TestOrthonormalize:
    """Tests for orthonormalization."""
    
    def test_orthonormalization(self):
        # Create a non-orthogonal matrix
        tangent_matrix = np.array([
            [1.0, 0.0, 0.0],
            [1.0, 1.0, 0.0],
            [1.0, 1.0, 1.0]
        ])
        
        result = orthonormalize(tangent_matrix)
        
        # Check orthogonality: Q^T @ Q should be identity
        product = result.T @ result
        assert np.allclose(product, np.eye(3), atol=1e-6)
        
        # Check unit length columns
        for i in range(result.shape[1]):
            assert np.isclose(np.linalg.norm(result[:, i]), 1.0)
    
    def test_already_orthogonal(self):
        tangent_matrix = np.eye(3)
        result = orthonormalize(tangent_matrix)
        assert np.allclose(result, np.eye(3))


class TestComputeFTLESingleTrajectory:
    """Tests for single trajectory FTLE computation."""
    
    def test_short_trajectory(self):
        # Create a very short trajectory
        trajectory = np.random.randn(5, 15)  # 5 time steps, 5 oscillators (15 dims)
        baseline_lambda = 0.9
        window_size = 100
        
        ftle, is_valid, error_msg = compute_ftle_single_trajectory(
            trajectory, baseline_lambda, window_size
        )
        
        assert not is_valid
        assert error_msg is not None
        assert "too short" in error_msg.lower()
    
    def test_valid_trajectory(self):
        # Create a reasonable trajectory
        N = 2
        n_steps = 1000
        trajectory = np.random.randn(n_steps, 3 * N)
        baseline_lambda = 0.9
        window_size = 100
        
        ftle, is_valid, error_msg = compute_ftle_single_trajectory(
            trajectory, baseline_lambda, window_size
        )
        
        # Should compute a value
        assert isinstance(ftle, float)
        # May or may not be valid depending on randomness
        assert error_msg is None or is_valid is False


class TestRunSlidingWindowSweep:
    """Tests for sliding window sweep."""
    
    def test_multiple_window_sizes(self):
        N = 2
        n_steps = 2000
        trajectory = np.random.randn(n_steps, 3 * N)
        baseline_lambda = 0.9
        window_sizes = [100, 200, 500]
        
        results = run_sliding_window_sweep(trajectory, baseline_lambda, window_sizes)
        
        assert len(results) == len(window_sizes)
        
        # Check each result has correct window size
        for result, window_size in zip(results, window_sizes):
            assert result.T == window_size
            assert result.N == N
    
    def test_empty_window_sizes(self):
        trajectory = np.random.randn(100, 6)
        results = run_sliding_window_sweep(trajectory, 0.9, [])
        assert len(results) == 0


class TestComputeFTLEBatch:
    """Tests for batch FTLE computation."""
    
    def test_batch_processing(self):
        N = 2
        n_steps = 1000
        window_sizes = [100, 200]
        
        # Create 3 trajectories
        trajectories = [np.random.randn(n_steps, 3 * N) for _ in range(3)]
        trial_ids = [1, 2, 3]
        baseline_lambda = 0.9
        sigma = 0.05
        
        results = compute_ftle_batch(
            trajectories, baseline_lambda, window_sizes,
            trial_ids, N, sigma
        )
        
        # Should have 3 trajectories * 2 window sizes = 6 results
        assert len(results) == 6
        
        # Check metadata
        for result in results:
            assert result.N == N
            assert result.sigma == sigma
            assert result.T in window_sizes
    
    def test_single_trajectory(self):
        N = 1
        n_steps = 500
        trajectory = [np.random.randn(n_steps, 3 * N)]
        results = compute_ftle_batch(
            trajectory, 0.9, [100], [1], N, 0.0
        )
        assert len(results) == 1
        assert results[0].trial_id == 1


class TestFTLEResultDataclass:
    """Tests for FTLEResult dataclass."""
    
    def test_creation(self):
        result = FTLEResult(
            trial_id=1,
            N=5,
            sigma=0.1,
            T=500,
            lambda_ftle=0.95,
            is_valid=True,
            error_message=None
        )
        
        assert result.trial_id == 1
        assert result.N == 5
        assert result.sigma == 0.1
        assert result.T == 500
        assert result.lambda_ftle == 0.95
        assert result.is_valid is True
        assert result.error_message is None
    
    def test_invalid_result(self):
        result = FTLEResult(
            trial_id=2,
            N=3,
            sigma=0.5,
            T=1000,
            lambda_ftle=0.0,
            is_valid=False,
            error_message="Divergence detected"
        )
        
        assert result.is_valid is False
        assert result.error_message == "Divergence detected"
