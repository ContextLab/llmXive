"""
Unit tests for FTLE computation module.
"""

import numpy as np
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import json
import tempfile

# Import module under test
from analysis.ftle import (
    compute_jacobian,
    propagate_tangent_vectors,
    orthonormalize,
    compute_ftle_single_trajectory,
    compute_ftle_batch,
    FTLEResult
)
from data.generator import TrajectoryData
from analysis.baseline import NonChaoticSystemError, BaselineConvergenceError
from analysis.shadowing import ShadowingCheckError


class TestJacobianComputation:
    """Tests for Jacobian matrix computation."""

    def test_jacobian_shape_single_lorenz(self):
        """Test that Jacobian has correct shape for single Lorenz oscillator."""
        state = np.array([1.0, 1.0, 1.0])
        params = {'sigma': 10.0, 'rho': 28.0, 'beta': 8/3, 'coupling': 0.0}

        jacobian = compute_jacobian(state, params)

        assert jacobian.shape == (3, 3)
        assert not np.any(np.isnan(jacobian))
        assert not np.any(np.isinf(jacobian))

    def test_jacobian_coupled_system(self):
        """Test Jacobian for coupled Lorenz system (N=2)."""
        state = np.array([1.0, 1.0, 1.0, 2.0, 2.0, 2.0])
        params = {
            'sigma': 10.0,
            'rho': 28.0,
            'beta': 8/3,
            'coupling': 0.1,
            'coupling_topology': 'ring'
        }

        jacobian = compute_jacobian(state, params)

        assert jacobian.shape == (6, 6)
        assert not np.any(np.isnan(jacobian))
        assert not np.any(np.isinf(jacobian))

        # Check that coupling terms are present
        # For ring topology with N=2, each oscillator couples to the other
        assert jacobian[0, 3] == pytest.approx(0.1)  # x1 coupling to x2
        assert jacobian[0, 3] == pytest.approx(-0.1) or jacobian[0, 3] == pytest.approx(0.1)  # Direction depends on implementation

    def test_jacobian_symmetry_properties(self):
        """Test that Jacobian has expected structure (not symmetric, but specific patterns)."""
        state = np.array([1.0, 1.0, 1.0])
        params = {'sigma': 10.0, 'rho': 28.0, 'beta': 8/3, 'coupling': 0.0}

        jacobian = compute_jacobian(state, params)

        # Diagonal elements should be negative (dissipative)
        assert jacobian[0, 0] < 0  # -sigma
        assert jacobian[1, 1] < 0  # -1
        assert jacobian[2, 2] < 0  # -beta


class TestTangentPropagation:
    """Tests for tangent vector propagation."""

    def test_propagation_preserves_dimension(self):
        """Test that propagation preserves matrix dimensions."""
        jacobian = np.random.randn(6, 6)
        tangent_matrix = np.eye(6)
        dt = 0.01

        result = propagate_tangent_vectors(jacobian, tangent_matrix, dt)

        assert result.shape == (6, 6)
        assert not np.any(np.isnan(result))
        assert not np.any(np.isinf(result))

    def test_small_dt_approximation(self):
        """Test that small dt gives approximately identity update."""
        jacobian = np.zeros((3, 3))
        jacobian[0, 1] = 1.0  # Simple shear
        tangent_matrix = np.eye(3)
        dt = 1e-6

        result = propagate_tangent_vectors(jacobian, tangent_matrix, dt)

        # For small dt, result should be close to I + J*dt
        expected = np.eye(3) + jacobian * dt
        assert np.allclose(result, expected, rtol=1e-5)


class TestOrthonormalization:
    """Tests for Gram-Schmidt orthonormalization."""

    def test_orthonormal_columns(self):
        """Test that output has orthonormal columns."""
        np.random.seed(42)
        matrix = np.random.randn(5, 5)

        orthonormal, log_norms = orthonormalize(matrix)

        # Check orthonormality
        product = orthonormal.T @ orthonormal
        assert np.allclose(product, np.eye(5), atol=1e-10)

        # Check that log_norms has correct length
        assert len(log_norms) == 5

    def test_orthonormalization_handles_singular(self):
        """Test that orthonormalization handles near-singular matrices."""
        # Create a matrix with near-linear dependence
        matrix = np.eye(5)
        matrix[:, 4] = matrix[:, 0] + 1e-15  # Nearly dependent

        orthonormal, log_norms = orthonormalize(matrix)

        # Should still produce orthonormal columns
        product = orthonormal.T @ orthonormal
        assert np.allclose(product, np.eye(5), atol=1e-8)


class TestFTLESingleTrajectory:
    """Tests for single trajectory FTLE computation."""

    def test_ftle_result_structure(self):
        """Test that FTLEResult has all required fields."""
        result = FTLEResult(
            t_max=100.0,
            noise_level=0.01,
            max_lyapunov_exponent=0.9,
            full_spectrum=[0.9, 0.0, -0.5, -1.0, -1.5, -2.0],
            convergence_rate=0.9,
            shadowing_verified=True,
            trajectory_id="test_001",
            error_estimate=0.01
        )

        assert result.t_max == 100.0
        assert result.max_lyapunov_exponent == 0.9
        assert len(result.full_spectrum) == 6
        assert result.shadowing_verified is True

    @patch('analysis.ftle.load_trajectory')
    @patch('analysis.ftle.gate_for_ftle_calculation')
    @patch('analysis.ftle.validate_and_gate_for_baseline')
    def test_ftle_computation_basic(self, mock_validate, mock_gate, mock_load):
        """Test basic FTLE computation with mocked dependencies."""
        # Setup mock trajectory
        times = np.linspace(0, 100, 1000)
        states = np.random.randn(1000, 6) * 0.1  # Small perturbations around 0
        states[:, 0] = np.sin(times)  # Add some structure
        states[:, 3] = np.cos(times)

        trajectory_data = TrajectoryData(
            states=states,
            times=times,
            trajectory_id="test_traj",
            noise_level=0.01
        )

        mock_load.return_value = trajectory_data

        # Setup shadowing mock
        mock_gate_result = MagicMock()
        mock_gate_result.shadowing_verified = True
        mock_gate.return_value = mock_gate_result

        params = {
            'sigma': 10.0,
            'rho': 28.0,
            'beta': 8/3,
            'coupling': 0.0
        }

        result = compute_ftle_single_trajectory(trajectory_data, params, t_window=50.0)

        assert isinstance(result, FTLEResult)
        assert result.t_max == 50.0
        assert result.noise_level == 0.01
        assert result.trajectory_id == "test_traj"
        assert result.shadowing_verified is True

    @patch('analysis.ftle.load_trajectory')
    @patch('analysis.ftle.validate_and_gate_for_baseline')
    def test_ftle_non_chaotic_detection(self, mock_validate, mock_load):
        """Test that non-chaotic systems are detected (lambda_max <= 0)."""
        from analysis.baseline import NonChaoticSystemError

        mock_validate.side_effect = NonChaoticSystemError("Non-chaotic regime detected")

        with pytest.raises(NonChaoticSystemError):
            compute_ftle_batch(["test_001"], t_window=100.0)


class TestFTLEBatch:
    """Tests for batch FTLE computation."""

    @patch('analysis.ftle.validate_and_gate_for_baseline')
    @patch('analysis.ftle.load_trajectory')
    @patch('analysis.ftle.gate_for_ftle_calculation')
    def test_batch_processing(self, mock_gate, mock_load, mock_validate):
        """Test batch processing of multiple trajectories."""
        # Setup mocks
        mock_validate.return_value = None

        mock_gate_result = MagicMock()
        mock_gate_result.shadowing_verified = True
        mock_gate.return_value = mock_gate_result

        # Create mock trajectories
        def create_mock_traj(traj_id):
            times = np.linspace(0, 50, 500)
            states = np.random.randn(500, 6) * 0.1
            return TrajectoryData(
                states=states,
                times=times,
                trajectory_id=traj_id,
                noise_level=0.01
            )

        mock_load.side_effect = lambda x: create_mock_traj(x)

        trajectory_ids = ["traj_001", "traj_002", "traj_003"]

        results = compute_ftle_batch(trajectory_ids, t_window=50.0)

        assert len(results) == 3
        assert all(isinstance(r, FTLEResult) for r in results)
        assert all(r.shadowing_verified for r in results)

    @patch('analysis.ftle.validate_and_gate_for_baseline')
    def test_batch_handles_empty_list(self, mock_validate):
        """Test that batch processing handles empty trajectory list."""
        mock_validate.return_value = None

        results = compute_ftle_batch([], t_window=100.0)

        assert results == []


class TestIntegrationFTLE:
    """Integration tests for FTLE module."""

    def test_ftle_convergence_on_clean_trajectory(self):
        """
        Test that FTLE converges to numerically computed asymptotic baseline
        for clean system as T increases (error < 5% at T=5000).

        This is a simplified test that verifies the algorithm structure.
        A full test would require actual trajectory data.
        """
        # Create a synthetic trajectory that should have known Lyapunov behavior
        # For this test, we use a simple oscillatory system with known properties
        N = 1
        dim = 3 * N

        # Generate times and states
        t_max = 1000
        dt = 0.01
        times = np.arange(0, t_max, dt)

        # Create a trajectory with exponential divergence (simple model)
        # lambda = 0.5 (positive Lyapunov exponent)
        lambda_true = 0.5
        states = np.zeros((len(times), dim))
        initial_condition = np.random.randn(dim) * 0.1

        for i, t in enumerate(times):
            # Simple exponential growth model for testing
            states[i] = initial_condition * np.exp(lambda_true * t)

        trajectory_data = TrajectoryData(
            states=states,
            times=times,
            trajectory_id="synthetic_test",
            noise_level=0.0
        )

        params = {
            'sigma': 10.0,
            'rho': 28.0,
            'beta': 8/3,
            'coupling': 0.0
        }

        # Compute FTLE for different window sizes
        t_windows = [100, 500, 1000]
        results = []

        for t_window in t_windows:
            result = compute_ftle_single_trajectory(trajectory_data, params, t_window)
            results.append(result.max_lyapunov_exponent)

        # Verify that computed exponents are positive (chaotic behavior)
        assert all(r > 0 for r in results), "Lyapunov exponents should be positive for chaotic system"

        # The exponents should be in the same ballpark (within 50% for this simple test)
        # A real test would compare against a computed baseline
        max_deviation = max(results) / min(results)
        assert max_deviation < 2.0, "Lyapunov exponents should be relatively stable across window sizes"

    def test_jacobian_propagation_stability(self):
        """Test that Jacobian propagation does not produce NaN/Inf in tangent vectors."""
        # Create a trajectory with extreme values to test numerical stability
        times = np.linspace(0, 100, 1000)
        states = np.random.randn(1000, 6) * 0.1

        # Add some large values to test boundedness
        states[100:200, 0] = 10.0

        trajectory_data = TrajectoryData(
            states=states,
            times=times,
            trajectory_id="stability_test",
            noise_level=0.01
        )

        params = {
            'sigma': 10.0,
            'rho': 28.0,
            'beta': 8/3,
            'coupling': 0.0
        }

        result = compute_ftle_single_trajectory(trajectory_data, params, t_window=50.0)

        # Verify no NaN/Inf in results
        assert not np.isnan(result.max_lyapunov_exponent)
        assert not np.isinf(result.max_lyapunov_exponent)
        assert all(not np.isnan(exp) for exp in result.full_spectrum)
        assert all(not np.isinf(exp) for exp in result.full_spectrum)
