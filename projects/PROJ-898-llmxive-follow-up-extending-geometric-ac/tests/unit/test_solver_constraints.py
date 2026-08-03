import pytest
import numpy as np
import torch
import logging
import os
import sys

# Ensure code/ is in path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.symbolic_solver import ConstraintMatrix, SymbolicSolver, TimeoutError
from code.config import load_config, SolverConfig
from code.utils import set_deterministic_seed

@pytest.fixture
def solver_config():
    """Load configuration for solver tests."""
    set_deterministic_seed(42)
    return load_config()

@pytest.fixture
def sample_constraint_matrix():
    """Create a sample constraint matrix for testing."""
    # Simulate a simple non-penetration constraint setup
    # Matrix shape: (num_constraints, num_variables)
    num_constraints = 10
    num_variables = 6  # 3D position + 3D orientation
    matrix = np.random.randn(num_constraints, num_variables).astype(np.float32)
    bounds = np.array([[-1.0, 1.0]] * num_constraints, dtype=np.float32)
    return matrix, bounds

class TestConstraintMatrix:
    """Unit tests for ConstraintMatrix functionality."""

    def test_initialization(self):
        """Test ConstraintMatrix initialization."""
        matrix = np.eye(5)
        bounds = np.array([[-1, 1]] * 5)
        cm = ConstraintMatrix(matrix, bounds)
        
        assert cm.constraint_matrix.shape == (5, 5)
        assert cm.bounds.shape == (5, 2)
        assert cm.num_constraints == 5
        assert cm.num_variables == 5

    def test_invalid_dimensions(self):
        """Test that mismatched dimensions raise an error."""
        matrix = np.random.randn(5, 3)
        bounds = np.array([[-1, 1]] * 4)  # Wrong number of constraints
        
        with pytest.raises(ValueError):
            ConstraintMatrix(matrix, bounds)

    def test_bounds_validation(self):
        """Test bounds validation (lower <= upper)."""
        matrix = np.eye(3)
        invalid_bounds = np.array([[1.0, -1.0], [-1, 1], [-1, 1]])  # First row invalid
        
        with pytest.raises(ValueError):
            ConstraintMatrix(matrix, invalid_bounds)

    def test_constraint_satisfaction_check(self, sample_constraint_matrix):
        """Test checking if a solution satisfies constraints."""
        matrix, bounds = sample_constraint_matrix
        cm = ConstraintMatrix(matrix, bounds)
        
        # Create a solution that satisfies constraints
        solution = np.zeros(matrix.shape[1])
        result = cm.check_satisfaction(solution)
        
        assert result['satisfied'] is True
        assert result['violated_indices'] == []

        # Create a solution that violates constraints
        solution_violated = np.ones(matrix.shape[1]) * 10.0
        result_violated = cm.check_satisfaction(solution_violated)
        
        assert result_violated['satisfied'] is False
        assert len(result_violated['violated_indices']) > 0

    def test_jacobian_computation(self):
        """Test Jacobian computation for constraint gradients."""
        num_constraints = 8
        num_variables = 4
        matrix = np.random.randn(num_constraints, num_variables)
        bounds = np.array([[-1.0, 1.0]] * num_constraints)
        
        cm = ConstraintMatrix(matrix, bounds)
        jacobian = cm.get_jacobian()
        
        assert jacobian.shape == (num_constraints, num_variables)
        np.testing.assert_array_almost_equal(jacobian, matrix)

class TestSymbolicSolver:
    """Unit tests for SymbolicSolver functionality."""

    def test_solver_initialization(self, solver_config):
        """Test SymbolicSolver initialization with valid config."""
        solver = SymbolicSolver(solver_config.solver)
        
        assert solver.config is not None
        assert solver.timeout_handler is not None
        assert solver.constraint_matrix is None

    def test_constraint_matrix_setter(self, solver_config, sample_constraint_matrix):
        """Test setting constraint matrix on solver."""
        solver = SymbolicSolver(solver_config.solver)
        matrix, bounds = sample_constraint_matrix
        
        solver.set_constraint_matrix(matrix, bounds)
        
        assert solver.constraint_matrix is not None
        assert solver.constraint_matrix.num_constraints == matrix.shape[0]

    def test_solve_with_timeout(self, solver_config):
        """Test solver timeout behavior."""
        solver = SymbolicSolver(solver_config.solver)
        
        # Set a very short timeout
        solver.config.timeout_seconds = 0.001
        
        # Create a constraint matrix that would take time to solve
        # (simulated by a large matrix)
        large_matrix = np.random.randn(1000, 500)
        bounds = np.array([[-1.0, 1.0]] * 1000)
        
        solver.set_constraint_matrix(large_matrix, bounds)
        
        with pytest.raises(TimeoutError):
            solver.solve()

    def test_solve_feasible_problem(self, solver_config):
        """Test solving a simple feasible problem."""
        solver = SymbolicSolver(solver_config.solver)
        
        # Simple identity constraint: x = 0
        matrix = np.eye(3)
        bounds = np.array([[0.0, 0.0]] * 3)
        
        solver.set_constraint_matrix(matrix, bounds)
        
        result = solver.solve()
        
        assert result['success'] is True
        np.testing.assert_array_almost_equal(result['solution'], np.zeros(3))

    def test_solve_infeasible_problem(self, solver_config):
        """Test handling of infeasible problems."""
        solver = SymbolicSolver(solver_config.solver)
        
        # Infeasible constraints: x >= 5 AND x <= 3
        matrix = np.array([[1.0], [-1.0]])
        bounds = np.array([[5.0, np.inf], [-np.inf, -3.0]])
        
        solver.set_constraint_matrix(matrix, bounds)
        
        result = solver.solve()
        
        assert result['success'] is False
        assert result['infeasible'] is True

    def test_non_penetration_constraints(self, solver_config):
        """Test non-penetration constraint generation."""
        solver = SymbolicSolver(solver_config.solver)
        
        # Simulate two objects that should not penetrate
        # Object 1 at (0, 0, 0) with radius 1
        # Object 2 at (3, 0, 0) with radius 1
        # Constraint: distance >= 2
        
        # Simple 1D constraint: x2 - x1 >= 2
        matrix = np.array([[-1.0, 1.0]])
        bounds = np.array([[2.0, np.inf]])
        
        solver.set_constraint_matrix(matrix, bounds)
        
        result = solver.solve()
        
        assert result['success'] is True
        # Solution should satisfy x2 - x1 >= 2
        assert result['solution'][1] - result['solution'][0] >= 2.0

    def test_joint_limit_constraints(self, solver_config):
        """Test joint limit constraint enforcement."""
        solver = SymbolicSolver(solver_config.solver)
        
        # Joint limits: -pi <= theta <= pi
        matrix = np.eye(1)
        bounds = np.array([[-np.pi, np.pi]])
        
        solver.set_constraint_matrix(matrix, bounds)
        
        result = solver.solve()
        
        assert result['success'] is True
        assert -np.pi <= result['solution'][0] <= np.pi

    def test_multiple_constraint_types(self, solver_config):
        """Test combining multiple constraint types."""
        solver = SymbolicSolver(solver_config.solver)
        
        # Combine joint limits and non-penetration
        # Joint 1: -pi <= theta1 <= pi
        # Joint 2: -pi <= theta2 <= pi
        # Non-penetration: theta2 - theta1 >= 0.5
        
        matrix = np.array([
            [1.0, 0.0],  # theta1 >= -pi
            [-1.0, 0.0],  # theta1 <= pi
            [0.0, 1.0],  # theta2 >= -pi
            [0.0, -1.0],  # theta2 <= pi
            [-1.0, 1.0]  # theta2 - theta1 >= 0.5
        ])
        bounds = np.array([
            [-np.pi, np.inf],
            [-np.inf, np.pi],
            [-np.pi, np.inf],
            [-np.inf, np.pi],
            [0.5, np.inf]
        ])
        
        solver.set_constraint_matrix(matrix, bounds)
        
        result = solver.solve()
        
        assert result['success'] is True
        # Verify all constraints are satisfied
        theta1, theta2 = result['solution']
        assert -np.pi <= theta1 <= np.pi
        assert -np.pi <= theta2 <= np.pi
        assert theta2 - theta1 >= 0.5

class TestSolverIntegration:
    """Integration tests for solver with configuration."""

    def test_solver_with_config_defaults(self):
        """Test solver uses default config values correctly."""
        config = load_config()
        solver = SymbolicSolver(config.solver)
        
        assert solver.config.timeout_seconds == config.solver.timeout_seconds
        assert solver.config.max_iterations == config.solver.max_iterations

    def test_solver_error_logging(self, solver_config, caplog):
        """Test that solver errors are properly logged."""
        solver = SymbolicSolver(solver_config.solver)
        
        # Set up logging capture
        with caplog.at_level(logging.ERROR):
            # Try to solve with invalid constraints
            matrix = np.array([[1.0]])
            bounds = np.array([[5.0, 3.0]])  # Invalid: lower > upper
            
            solver.set_constraint_matrix(matrix, bounds)
            
            with pytest.raises(ValueError):
                solver.solve()
            
            assert "Invalid bounds" in caplog.text or "constraint" in caplog.text.lower()

    def test_solver_performance_baseline(self, solver_config):
        """Test solver performance on a baseline problem."""
        solver = SymbolicSolver(solver_config.solver)
        
        # Standard test problem
        num_vars = 50
        num_constraints = 100
        
        matrix = np.random.randn(num_constraints, num_vars)
        bounds = np.array([[-1.0, 1.0]] * num_constraints)
        
        solver.set_constraint_matrix(matrix, bounds)
        
        import time
        start = time.time()
        result = solver.solve()
        elapsed = time.time() - start
        
        # Should complete within timeout
        assert elapsed < solver.config.timeout_seconds
        assert result['success'] is True
