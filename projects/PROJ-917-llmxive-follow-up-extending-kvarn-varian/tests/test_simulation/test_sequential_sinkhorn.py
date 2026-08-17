import pytest
import numpy as np
from simulation.sequential_sinkhorn import SequentialSinkhornSolver
from simulation.state import SimulationState

class TestSequentialSinkhornSolver:
    """
    Tests for the SequentialSinkhornSolver class.
    """

    def test_solve_step_updates_state(self):
        """Test that solve_step correctly updates the SimulationState."""
        solver = SequentialSinkhornSolver(epsilon=1e-6)
        
        # Create a dummy 4x4 matrix
        np.random.seed(42)
        matrix = np.random.rand(4, 4)
        matrix = matrix / np.sum(matrix, axis=1, keepdims=True)
        
        # Initial state
        initial_state = SimulationState(
            accumulated_kl=0.0,
            current_error_state={},
            step_index=0,
            full_trajectory=[]
        )
        
        # Solve step
        scaling_factor, new_state = solver.solve_step(matrix, initial_state)
        
        # Verify scaling factor is a float
        assert isinstance(scaling_factor, float)
        assert scaling_factor > 0
        
        # Verify state updates
        assert new_state.step_index == 1
        assert len(new_state.full_trajectory) == 1
        assert new_state.accumulated_kl > 0
        assert "kl_div" in new_state.current_error_state
        assert "scaling_factor" in new_state.current_error_state

    def test_accumulated_kl_increases(self):
        """Test that accumulated KL increases over multiple steps."""
        solver = SequentialSinkhornSolver(epsilon=1e-6)
        
        # Create two dummy matrices
        np.random.seed(42)
        matrix1 = np.random.rand(4, 4)
        matrix1 = matrix1 / np.sum(matrix1, axis=1, keepdims=True)
        
        matrix2 = np.random.rand(4, 4)
        matrix2 = matrix2 / np.sum(matrix2, axis=1, keepdims=True)
        
        # Initial state
        state = SimulationState(
            accumulated_kl=0.0,
            current_error_state={},
            step_index=0,
            full_trajectory=[]
        )
        
        # Step 1
        _, state = solver.solve_step(matrix1, state)
        kl_after_step1 = state.accumulated_kl
        
        # Step 2
        _, state = solver.solve_step(matrix2, state)
        kl_after_step2 = state.accumulated_kl
        
        # Verify accumulation
        assert kl_after_step2 > kl_after_step1
        assert state.step_index == 2
        assert len(state.full_trajectory) == 2

    def test_solve_step_handles_small_epsilon(self):
        """Test that solver handles small epsilon values correctly."""
        solver = SequentialSinkhornSolver(epsilon=1e-8)
        
        np.random.seed(42)
        matrix = np.random.rand(4, 4)
        matrix = matrix / np.sum(matrix, axis=1, keepdims=True)
        
        state = SimulationState(
            accumulated_kl=0.0,
            current_error_state={},
            step_index=0,
            full_trajectory=[]
        )
        
        scaling_factor, new_state = solver.solve_step(matrix, state)
        
        assert isinstance(scaling_factor, float)
        assert new_state.step_index == 1
        assert new_state.accumulated_kl >= 0

    def test_solve_step_handles_large_epsilon(self):
        """Test that solver handles large epsilon values correctly."""
        solver = SequentialSinkhornSolver(epsilon=1e-3)
        
        np.random.seed(42)
        matrix = np.random.rand(4, 4)
        matrix = matrix / np.sum(matrix, axis=1, keepdims=True)
        
        state = SimulationState(
            accumulated_kl=0.0,
            current_error_state={},
            step_index=0,
            full_trajectory=[]
        )
        
        scaling_factor, new_state = solver.solve_step(matrix, state)
        
        assert isinstance(scaling_factor, float)
        assert new_state.step_index == 1
        assert new_state.accumulated_kl >= 0