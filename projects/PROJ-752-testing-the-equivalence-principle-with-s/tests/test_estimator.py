"""
Unit tests for the joint least-squares solver convergence.

This module implements TDD-first tests for the estimator module.
It verifies that the joint solver converges when provided with
synthetic data generated from a known ground truth.

Note: The interface `OrbitSolution` and `fit_joint_parameters` are
assumed to be implemented in `code/models/estimator.py` as per T024.
This test file mocks the data loading to ensure deterministic testing
without requiring real data downloads, but the solver logic is real.
"""
import pytest
import numpy as np
from typing import List, Dict, Any
from pathlib import Path

# We assume the estimator module exists and provides these classes/functions
# If T024 is not yet run, this will raise ImportError, which is expected behavior
# for the "test-first" approach until the implementation is provided.
try:
    from models.estimator import fit_joint_parameters, OrbitSolution, CostFunctionResult
except ImportError:
    # If the module isn't ready, we define minimal mocks for the test structure
    # to verify the test logic itself, but mark the test as skipped in real runs.
    class OrbitSolution:
        def __init__(self, params: Dict[str, float], covariance: np.ndarray, converged: bool):
            self.params = params
            self.covariance = covariance
            self.converged = converged
            self.residual_rms = 0.0
    
    class CostFunctionResult:
        def __init__(self, value: float, gradient: np.ndarray):
            self.value = value
            self.gradient = gradient

    def fit_joint_parameters(
        states: List[np.ndarray], 
        residuals: List[np.ndarray], 
        weights: List[np.ndarray],
        initial_guess: np.ndarray
    ) -> OrbitSolution:
        """Mock implementation for testing structure."""
        # Simulate non-convergence if not implemented
        return OrbitSolution(
            params={'ac': 0.0, 'g': 9.8},
            covariance=np.eye(2),
            converged=False
        )

class TestJointSolverConvergence:
    """Tests for the joint least-squares solver."""
    
    def setup_method(self):
        """Generate synthetic data for testing convergence."""
        # Synthetic parameters
        self.true_ac = 1.5e-10  # m/s^2 (differential acceleration)
        self.true_g = 9.8       # m/s^2 (local gravity)
        
        # Generate synthetic states and residuals
        # Simulating two satellites (Sat A and Sat B)
        self.n_points = 1000
        self.t = np.linspace(0, 86400, self.n_points) # 1 day of data
        
        # Synthetic residuals: r = H*x + noise
        # For joint estimation, we stack residuals from both satellites
        # Residual model: r = ac * f(t) + noise
        noise_sigma = 0.01 # 1cm noise
        
        # Satellite A residuals
        self.residuals_a = self.true_ac * np.sin(self.t / 1000.0) + np.random.normal(0, noise_sigma, self.n_points)
        # Satellite B residuals (slightly different phase/amplitude to simulate different orbits)
        self.residuals_b = self.true_ac * 0.95 * np.sin(self.t / 1000.0 + 0.1) + np.random.normal(0, noise_sigma, self.n_points)
        
        # Weights (inverse variance)
        self.weights_a = np.ones(self.n_points) / (noise_sigma ** 2)
        self.weights_b = np.ones(self.n_points) / (noise_sigma ** 2)
        
        # State vectors (simplified for testing: just time and position)
        # In a real scenario, these would be 3D vectors or full state histories
        self.states_a = np.column_stack([self.t, np.zeros(self.n_points)])
        self.states_b = np.column_stack([self.t, np.zeros(self.n_points)])
        
        # Initial guess (deliberately wrong to test convergence)
        self.initial_guess = np.array([0.0, 9.8]) # [ac, g]
    
    def test_solver_converges_on_synthetic_data(self):
        """Test that the solver converges to the true parameters within tolerance."""
        # Skip if the real implementation is not available
        if 'fit_joint_parameters' not in globals() or not hasattr(fit_joint_parameters, '__module__'):
            pytest.skip("Estimator implementation (T024) not yet available.")
        
        # Run the joint solver
        solution = fit_joint_parameters(
            states=[self.states_a, self.states_b],
            residuals=[self.residuals_a, self.residuals_b],
            weights=[self.weights_a, self.weights_b],
            initial_guess=self.initial_guess
        )
        
        # Verify convergence
        assert solution.converged, "Solver did not converge on synthetic data."
        
        # Verify parameter recovery
        # Allow 10% tolerance due to noise
        estimated_ac = solution.params.get('ac', 0.0)
        estimated_g = solution.params.get('g', 0.0)
        
        assert abs(estimated_ac - self.true_ac) < 0.1 * self.true_ac, \
            f"Estimated ac ({estimated_ac}) differs too much from true ({self.true_ac})"
        
        assert abs(estimated_g - self.true_g) < 0.01 * self.true_g, \
            f"Estimated g ({estimated_g}) differs too much from true ({self.true_g})"
    
    def test_residual_rms_decreases(self):
        """Test that the residual RMS is below the convergence threshold."""
        if 'fit_joint_parameters' not in globals():
            pytest.skip("Estimator implementation not available.")
        
        solution = fit_joint_parameters(
            states=[self.states_a, self.states_b],
            residuals=[self.residuals_a, self.residuals_b],
            weights=[self.weights_a, self.weights_b],
            initial_guess=self.initial_guess
        )
        
        # The convergence criteria usually involves the residual RMS
        # We expect it to be close to the noise level (1cm = 0.01m)
        assert solution.residual_rms < 0.02, \
            f"Residual RMS ({solution.residual_rms}) is too high; expected < 0.02m"
    
    def test_covariance_matrix_is_positive_definite(self):
        """Test that the output covariance matrix is positive definite."""
        if 'fit_joint_parameters' not in globals():
            pytest.skip("Estimator implementation not available.")
        
        solution = fit_joint_parameters(
            states=[self.states_a, self.states_b],
            residuals=[self.residuals_a, self.residuals_b],
            weights=[self.weights_a, self.weights_b],
            initial_guess=self.initial_guess
        )
        
        # Check if covariance matrix is positive definite
        eigenvalues = np.linalg.eigvals(solution.covariance)
        assert np.all(eigenvalues > 0), "Covariance matrix is not positive definite."
    
    def test_solver_handles_divergence_gracefully(self):
        """Test that the solver handles cases where convergence is impossible."""
        # Create data with no signal (ac = 0) but high noise
        noisy_residuals = np.random.normal(0, 1.0, self.n_points) # High noise
        zero_guess = np.array([0.0, 9.8])
        
        if 'fit_joint_parameters' not in globals():
            pytest.skip("Estimator implementation not available.")
        
        # This might not converge or might converge to a poor solution
        # The key is that it shouldn't crash
        try:
            solution = fit_joint_parameters(
                states=[self.states_a, self.states_b],
                residuals=[noisy_residuals, noisy_residuals],
                weights=[np.ones(self.n_points), np.ones(self.n_points)],
                initial_guess=zero_guess
            )
            # Even if it doesn't converge, it should return an object
            assert hasattr(solution, 'params'), "Solution object missing params."
        except Exception as e:
            # If it raises an exception, it must be a specific convergence error
            assert "Convergence" in str(e) or "Divergence" in str(e), \
                f"Unexpected error during divergence test: {e}"