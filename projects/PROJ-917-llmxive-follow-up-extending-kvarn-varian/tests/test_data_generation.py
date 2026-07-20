"""
Unit tests for data generation components, including the Sequential Sinkhorn solver.
"""
import pytest
import numpy as np
from typing import List, Dict, Any, Tuple
import sys
import os

# Add code directory to path for imports if running standalone
if "code" not in sys.path:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "code"))

from simulation.state import SimulationState
from simulation.sequential_sinkhorn import SequentialSinkhornSolver
from data_generation.utils import apply_epsilon_floor, check_numerical_stability
from config import get_config


class TestSequentialSinkhornSolver:
    """
    Unit tests for the Sequential Sinkhorn solver convergence and state update logic.
    """

    def setup_method(self):
        """Set up test fixtures."""
        self.config = get_config()
        self.solver = SequentialSinkhornSolver(
            max_iterations=self.config.SINKHORN_MAX_ITER,
            tolerance=self.config.SINKHORN_TOL,
            epsilon=self.config.EPSILON_FLOOR
        )

    def _create_test_matrix(self, shape: Tuple[int, int] = (128, 128), 
                             sparsity: float = 0.0, 
                             noise_level: float = 0.01) -> np.ndarray:
        """Create a test attention matrix with optional sparsity and noise."""
        matrix = np.random.rand(*shape)
        
        # Apply sparsity
        if sparsity > 0:
            mask = np.random.rand(*shape) > sparsity
            matrix = matrix * mask
        
        # Add noise
        if noise_level > 0:
            matrix += np.random.normal(0, noise_level, matrix.shape)
        
        # Ensure non-negative and apply epsilon floor
        matrix = np.maximum(matrix, self.config.EPSILON_FLOOR)
        
        return matrix

    def _create_initial_state(self, accumulated_kl: float = 0.0) -> SimulationState:
        """Create an initial simulation state."""
        return SimulationState(
            accumulated_kl=accumulated_kl,
            current_error_state={
                "step_index": 0,
                "last_scaling_factor": 0.0,
                "error_magnitude": 0.0
            },
            step_index=0
        )

    def test_solver_initialization(self):
        """Test that the solver initializes with correct parameters."""
        assert self.solver.max_iterations == self.config.SINKHORN_MAX_ITER
        assert self.solver.tolerance == self.config.SINKHORN_TOL
        assert self.solver.epsilon == self.config.EPSILON_FLOOR
        assert self.solver.converged is False
        assert self.solver.iterations == 0

    def test_solve_step_basic(self):
        """Test basic solve_step functionality with a simple matrix."""
        matrix = self._create_test_matrix(shape=(32, 32), sparsity=0.1)
        initial_state = self._create_initial_state()
        
        scaling_factor, new_state = self.solver.solve_step(matrix, initial_state)
        
        # Verify outputs
        assert isinstance(scaling_factor, float)
        assert scaling_factor > 0.0
        assert isinstance(new_state, SimulationState)
        
        # Verify state update
        assert new_state.step_index == 1
        assert new_state.current_error_state["step_index"] == 1
        assert new_state.current_error_state["last_scaling_factor"] == scaling_factor
        
        # Verify state is not the same object (immutable update pattern)
        assert new_state is not initial_state

    def test_solve_step_convergence(self):
        """Test that the solver converges within max iterations."""
        matrix = self._create_test_matrix(shape=(64, 64), sparsity=0.2)
        initial_state = self._create_initial_state()
        
        scaling_factor, new_state = self.solver.solve_step(matrix, initial_state)
        
        # Check convergence status
        assert self.solver.converged is True or self.solver.iterations <= self.config.SINKHORN_MAX_ITER
        
        # Verify iterations count
        assert 0 < self.solver.iterations <= self.config.SINKHORN_MAX_ITER

    def test_solve_step_state_accumulation(self):
        """Test that error accumulates correctly across multiple steps."""
        matrix = self._create_test_matrix(shape=(32, 32))
        state = self._create_initial_state(accumulated_kl=0.0)
        
        steps = 5
        accumulated_kls = []
        
        for i in range(steps):
            # Create a slightly different matrix each step to simulate drift
            step_matrix = matrix * (1.0 + 0.01 * i)
            _, new_state = self.solver.solve_step(step_matrix, state)
            
            accumulated_kls.append(new_state.accumulated_kl)
            state = new_state
        
        # Verify that accumulated KL is monotonically increasing (non-negative errors)
        for i in range(1, len(accumulated_kls)):
            assert accumulated_kls[i] >= accumulated_kls[i-1]
        
        # Verify final step index
        assert state.step_index == steps

    def test_solve_step_numerical_stability(self):
        """Test solver behavior with numerically challenging inputs."""
        # Test with very small values (near epsilon floor)
        small_matrix = np.full((32, 32), self.config.EPSILON_FLOOR * 1.1)
        state = self._create_initial_state()
        
        scaling_factor_small, _ = self.solver.solve_step(small_matrix, state)
        assert scaling_factor_small > 0.0
        assert np.isfinite(scaling_factor_small)
        
        # Test with large values
        large_matrix = np.full((32, 32), 1e6)
        state = self._create_initial_state()
        
        scaling_factor_large, _ = self.solver.solve_step(large_matrix, state)
        assert scaling_factor_large > 0.0
        assert np.isfinite(scaling_factor_large)
        
        # Test with sparse matrix (many zeros)
        sparse_matrix = self._create_test_matrix(shape=(32, 32), sparsity=0.9)
        state = self._create_initial_state()
        
        scaling_factor_sparse, _ = self.solver.solve_step(sparse_matrix, state)
        assert scaling_factor_sparse > 0.0
        assert np.isfinite(scaling_factor_sparse)

    def test_solve_step_deterministic_with_seed(self):
        """Test that solver produces deterministic results with fixed seed."""
        np.random.seed(42)
        matrix1 = self._create_test_matrix(shape=(32, 32))
        state1 = self._create_initial_state()
        
        np.random.seed(42)
        matrix2 = self._create_test_matrix(shape=(32, 32))
        state2 = self._create_initial_state()
        
        # Verify matrices are identical
        assert np.allclose(matrix1, matrix2)
        
        # Solve
        sf1, new_state1 = self.solver.solve_step(matrix1, state1)
        sf2, new_state2 = self.solver.solve_step(matrix2, state2)
        
        # Verify results are identical
        assert np.isclose(sf1, sf2)
        assert new_state1.accumulated_kl == new_state2.accumulated_kl
        assert new_state1.step_index == new_state2.step_index

    def test_solve_step_error_state_tracking(self):
        """Test that error state is correctly tracked and updated."""
        matrix = self._create_test_matrix(shape=(32, 32))
        state = self._create_initial_state()
        
        # Initial state checks
        assert state.current_error_state["step_index"] == 0
        assert state.current_error_state["last_scaling_factor"] == 0.0
        assert state.current_error_state["error_magnitude"] == 0.0
        
        # After one step
        _, new_state = self.solver.solve_step(matrix, state)
        
        assert new_state.current_error_state["step_index"] == 1
        assert new_state.current_error_state["last_scaling_factor"] > 0.0
        # Error magnitude should be non-negative
        assert new_state.current_error_state["error_magnitude"] >= 0.0

    def test_solve_step_tolerance_convergence(self):
        """Test that solver respects tolerance parameter for convergence."""
        # Create a matrix that should converge quickly
        matrix = np.ones((32, 32)) * 0.5
        state = self._create_initial_state()
        
        # Solve with default tolerance
        _, _ = self.solver.solve_step(matrix, state)
        
        # Verify convergence
        assert self.solver.converged is True
        
        # Reset solver with stricter tolerance
        strict_solver = SequentialSinkhornSolver(
            max_iterations=100,
            tolerance=1e-10,
            epsilon=self.config.EPSILON_FLOOR
        )
        
        _, _ = strict_solver.solve_step(matrix, state)
        assert strict_solver.converged is True
        # Should take more iterations for stricter tolerance
        assert strict_solver.iterations >= self.solver.iterations

    def test_solve_step_with_different_matrix_sizes(self):
        """Test solver with various matrix dimensions."""
        sizes = [(16, 16), (32, 32), (64, 64), (128, 128)]
        
        for rows, cols in sizes:
            matrix = self._create_test_matrix(shape=(rows, cols))
            state = self._create_initial_state()
            
            scaling_factor, new_state = self.solver.solve_step(matrix, state)
            
            assert scaling_factor > 0.0
            assert np.isfinite(scaling_factor)
            assert new_state.step_index == 1

    def test_solve_step_state_immutability(self):
        """Test that the original state is not modified."""
        matrix = self._create_test_matrix(shape=(32, 32))
        original_state = self._create_initial_state(accumulated_kl=5.0)
        
        # Store original values
        original_kl = original_state.accumulated_kl
        original_index = original_state.step_index
        
        # Solve
        _, new_state = self.solver.solve_step(matrix, original_state)
        
        # Verify original state is unchanged
        assert original_state.accumulated_kl == original_kl
        assert original_state.step_index == original_index
        assert original_state is not new_state

    def test_solve_step_return_types(self):
        """Test that solve_step returns correct types."""
        matrix = self._create_test_matrix(shape=(32, 32))
        state = self._create_initial_state()
        
        scaling_factor, new_state = self.solver.solve_step(matrix, state)
        
        assert isinstance(scaling_factor, (float, np.floating))
        assert isinstance(new_state, SimulationState)
        assert hasattr(new_state, 'accumulated_kl')
        assert hasattr(new_state, 'current_error_state')
        assert hasattr(new_state, 'step_index')


class TestSequentialSinkhornIntegration:
    """Integration tests for SequentialSinkhornSolver with other components."""

    def setup_method(self):
        self.solver = SequentialSinkhornSolver(
            max_iterations=50,
            tolerance=1e-6,
            epsilon=1e-6
        )

    def test_full_simulation_loop(self):
        """Test a full simulation loop with state propagation."""
        np.random.seed(123)
        state = SimulationState(
            accumulated_kl=0.0,
            current_error_state={"step_index": 0, "last_scaling_factor": 0.0, "error_magnitude": 0.0},
            step_index=0
        )
        
        trajectory = []
        for i in range(10):
            matrix = np.random.rand(32, 32)
            matrix = np.maximum(matrix, 1e-6)
            
            scaling_factor, state = self.solver.solve_step(matrix, state)
            
            trajectory.append({
                "step": i,
                "scaling_factor": scaling_factor,
                "accumulated_kl": state.accumulated_kl
            })
        
        # Verify trajectory structure
        assert len(trajectory) == 10
        assert trajectory[0]["step"] == 0
        assert trajectory[-1]["step"] == 9
        assert trajectory[-1]["accumulated_kl"] >= 0.0
        
        # Verify scaling factors are positive
        for entry in trajectory:
            assert entry["scaling_factor"] > 0.0

    def test_error_accumulation_across_steps(self):
        """Test that error accumulates correctly over multiple steps."""
        state = SimulationState(
            accumulated_kl=0.0,
            current_error_state={"step_index": 0, "last_scaling_factor": 0.0, "error_magnitude": 0.0},
            step_index=0
        )
        
        initial_kl = state.accumulated_kl
        
        for i in range(5):
            matrix = np.random.rand(32, 32) + 0.1
            _, state = self.solver.solve_step(matrix, state)
        
        # KL should have accumulated (non-decreasing)
        assert state.accumulated_kl >= initial_kl
        assert state.step_index == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])