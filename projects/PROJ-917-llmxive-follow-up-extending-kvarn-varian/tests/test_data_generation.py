"""
Test suite for data generation utilities, focusing on Sequential Sinkhorn solver
convergence and state update mechanisms.
"""
import pytest
import numpy as np
from typing import List, Tuple, Dict, Any
import json
import os
import sys
from pathlib import Path

# Add code root to path for imports if running directly
code_root = Path(__file__).parent.parent / "code"
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from simulation.sequential_sinkhorn import SequentialSinkhornSolver, SinkhornState
from data_generation.utils import apply_epsilon_floor, safe_divide
from shared.entities import AttentionTrajectory


class TestSequentialSinkhornSolver:
    """
    Unit tests for the Sequential Sinkhorn solver convergence and state update logic.
    """

    def setup_method(self):
        """Initialize test fixtures."""
        self.dummy_matrix = np.array([
            [0.1, 0.2, 0.3, 0.4],
            [0.4, 0.3, 0.2, 0.1],
            [0.2, 0.1, 0.4, 0.3]
        ], dtype=np.float64)
        
        self.dummy_vector = np.array([0.33, 0.33, 0.34], dtype=np.float64)
        
        # Initialize solver with standard parameters
        self.solver = SequentialSinkhornSolver(
            max_iterations=100,
            tolerance=1e-6,
            epsilon_floor=1e-10
        )

    def test_initialization(self):
        """Test that the solver initializes with correct default parameters."""
        assert self.solver.max_iterations == 100
        assert self.solver.tolerance == 1e-6
        assert self.solver.epsilon_floor == 1e-10
        assert self.solver.current_state is None

    def test_solve_convergence_simple(self):
        """
        Test that the solver converges on a simple, well-conditioned matrix.
        Verifies that the iterative process reduces the error below tolerance.
        """
        # Use a doubly stochastic target for easier convergence check
        # A simple matrix where rows and cols sum to 1 after normalization
        test_matrix = np.ones((3, 3), dtype=np.float64) / 3.0
        target_row_sum = np.ones(3, dtype=np.float64)
        target_col_sum = np.ones(3, dtype=np.float64)

        state = self.solver.solve(
            matrix=test_matrix,
            target_row_sum=target_row_sum,
            target_col_sum=target_col_sum
        )

        # Check convergence flag
        assert state.converged is True, "Solver should converge on a well-conditioned matrix"
        
        # Check iteration count is reasonable (not hitting max immediately)
        assert state.iterations < self.solver.max_iterations

    def test_state_update_logic(self):
        """
        Test that the state object correctly tracks cumulative error and iterations.
        """
        # Create a scenario that takes a few iterations
        # Slightly perturb a uniform matrix to force convergence steps
        base = np.ones((4, 4), dtype=np.float64) * 0.25
        base[0, 0] += 0.1
        base[0, 1] -= 0.1
        
        target_row = np.ones(4, dtype=np.float64)
        target_col = np.ones(4, dtype=np.float64)

        state = self.solver.solve(
            matrix=base,
            target_row_sum=target_row,
            target_col_sum=target_col
        )

        # Verify state attributes are populated
        assert isinstance(state.iterations, int)
        assert state.iterations > 0
        assert isinstance(state.final_error, float)
        assert state.final_error >= 0.0
        assert state.converged is True

    def test_epsilon_floor_application(self):
        """
        Test that the solver applies epsilon floor to prevent division by zero
        and numerical instability during iterations.
        """
        # Create a matrix with very small values
        tiny_matrix = np.ones((2, 2), dtype=np.float64) * 1e-15
        tiny_matrix[0, 0] = 0.5
        tiny_matrix[1, 1] = 0.5
        
        target_row = np.ones(2, dtype=np.float64) * 0.5
        target_col = np.ones(2, dtype=np.float64) * 0.5

        # This should not raise an exception due to epsilon flooring
        state = self.solver.solve(
            matrix=tiny_matrix,
            target_row_sum=target_row,
            target_col_sum=target_col
        )

        # Check that the result is finite
        assert np.all(np.isfinite(state.result_matrix))
        assert state.converged is True

    def test_max_iterations_reached(self):
        """
        Test behavior when max iterations are reached before convergence.
        """
        # Create a solver with very low max iterations to force early exit
        constrained_solver = SequentialSinkhornSolver(
            max_iterations=1,
            tolerance=1e-9, # Very strict tolerance
            epsilon_floor=1e-10
        )
        
        # Use a matrix that requires more than 1 iteration to converge
        test_matrix = np.array([
            [0.1, 0.9],
            [0.9, 0.1]
        ], dtype=np.float64)
        
        target_row = np.array([0.5, 0.5], dtype=np.float64)
        target_col = np.array([0.5, 0.5], dtype=np.float64)

        state = constrained_solver.solve(
            matrix=test_matrix,
            target_row_sum=target_row,
            target_col_sum=target_col
        )

        assert state.iterations == 1
        assert state.converged is False

    def test_result_matrix_properties(self):
        """
        Test that the resulting matrix satisfies row and column sum constraints.
        """
        test_matrix = np.random.rand(5, 5).astype(np.float64)
        test_matrix = test_matrix / test_matrix.sum() # Normalize to sum to 1 roughly
        
        target_row = np.ones(5, dtype=np.float64) / 5.0
        target_col = np.ones(5, dtype=np.float64) / 5.0

        state = self.solver.solve(
            matrix=test_matrix,
            target_row_sum=target_row,
            target_col_sum=target_col
        )

        result = state.result_matrix
        
        # Check row sums
        row_sums = result.sum(axis=1)
        np.testing.assert_allclose(row_sums, target_row, rtol=1e-4, atol=1e-4)
        
        # Check column sums
        col_sums = result.sum(axis=0)
        np.testing.assert_allclose(col_sums, target_col, rtol=1e-4, atol=1e-4)

    def test_state_serialization(self):
        """
        Test that the SinkhornState can be serialized to JSON for logging.
        """
        state = self.solver.solve(
            matrix=self.dummy_matrix,
            target_row_sum=np.ones(3, dtype=np.float64) / 3.0,
            target_col_sum=np.ones(3, dtype=np.float64) / 3.0
        )

        # Convert to dict
        state_dict = {
            "iterations": state.iterations,
            "final_error": state.final_error,
            "converged": state.converged,
            "result_shape": list(state.result_matrix.shape)
        }

        # Ensure it can be JSON serialized
        json_str = json.dumps(state_dict)
        assert isinstance(json_str, str)

    def test_numerical_stability_with_zeros(self):
        """
        Test solver behavior when input matrix contains zeros.
        """
        sparse_matrix = np.array([
            [0.0, 0.5, 0.5],
            [0.5, 0.0, 0.5],
            [0.5, 0.5, 0.0]
        ], dtype=np.float64)

        target_row = np.ones(3, dtype=np.float64) / 3.0
        target_col = np.ones(3, dtype=np.float64) / 3.0

        # Should handle zeros via epsilon floor logic internally
        state = self.solver.solve(
            matrix=sparse_matrix,
            target_row_sum=target_row,
            target_col_sum=target_col
        )

        assert np.all(np.isfinite(state.result_matrix))
        assert state.converged is True

class TestSequentialSinkhornIntegration:
    """
    Integration tests linking Sinkhorn solver with data generation concepts.
    """

    def test_sinkhorn_in_attention_trajectory_context(self):
        """
        Verify that the solver can process matrices derived from attention trajectories.
        """
        # Simulate an attention matrix (softmax output usually)
        logits = np.random.rand(10, 10).astype(np.float64)
        attention_matrix = np.exp(logits)
        attention_matrix = attention_matrix / attention_matrix.sum(axis=1, keepdims=True)

        # Define target marginals (e.g., uniform distribution over tokens)
        n = attention_matrix.shape[0]
        target_row = np.ones(n, dtype=np.float64) / n
        target_col = np.ones(n, dtype=np.float64) / n

        solver = SequentialSinkhornSolver(max_iterations=50, tolerance=1e-5)
        state = solver.solve(
            matrix=attention_matrix,
            target_row_sum=target_row,
            target_col_sum=target_col
        )

        # Verify the output is a valid probability matrix (non-negative, sums correct)
        assert np.all(state.result_matrix >= 0)
        assert np.allclose(state.result_matrix.sum(), 1.0)

    def test_cumulative_error_tracking(self):
        """
        Test that the solver tracks error reduction over iterations.
        """
        # We can't easily inspect internal iteration history without modifying the solver,
        # but we can verify that the final error is significantly lower than a naive baseline
        # or that it meets the tolerance.
        
        test_matrix = np.random.rand(4, 4).astype(np.float64)
        target = np.ones(4, dtype=np.float64) / 4.0
        
        solver = SequentialSinkhornSolver(max_iterations=100, tolerance=1e-6)
        state = solver.solve(test_matrix, target, target)

        # The final error should be below tolerance if converged
        if state.converged:
            assert state.final_error <= solver.tolerance
        
        # If not converged (unlikely with random matrix and 100 iters), error should still be reasonable
        assert state.final_error < 1.0 # Sanity check

if __name__ == "__main__":
    pytest.main([__file__, "-v"])