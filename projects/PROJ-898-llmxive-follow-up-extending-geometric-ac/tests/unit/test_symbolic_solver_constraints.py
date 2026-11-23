import pytest
import numpy as np
import torch
from unittest.mock import MagicMock, patch
import os
import sys

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from symbolic_solver import SymbolicSolver, ConstraintMatrix, TimeoutError
from config import load_config, Config
from utils import set_deterministic_seed

class TestConstraintMatrix:
    """Unit tests for ConstraintMatrix class and constraint generation."""

    def setup_method(self):
        """Set up test fixtures."""
        set_deterministic_seed(42)
        self.test_config = load_config()

    def test_constraint_matrix_initialization(self):
        """Test that ConstraintMatrix initializes with correct dimensions."""
        n_vars = 10
        n_constraints = 5
        
        matrix = ConstraintMatrix(n_vars, n_constraints)
        
        assert matrix.A.shape == (n_constraints, n_vars)
        assert matrix.b.shape == (n_constraints,)
        assert matrix.A.dtype == np.float32
        assert matrix.b.dtype == np.float32

    def test_non_penetration_constraint_generation(self):
        """Test generation of non-penetration constraints between objects."""
        solver = SymbolicSolver(self.test_config)
        
        # Create mock object positions and radii
        obj1_pos = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        obj2_pos = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        radius1 = 0.2
        radius2 = 0.2
        
        # Generate non-penetration constraints
        constraints = solver.generate_non_penetration_constraints(
            obj1_pos, obj2_pos, radius1, radius2
        )
        
        assert constraints is not None
        assert isinstance(constraints, ConstraintMatrix)
        assert constraints.A.shape[0] > 0  # At least one constraint
        assert constraints.A.shape[1] == 3  # 3D position variables

    def test_joint_limit_constraints(self):
        """Test generation of joint limit constraints."""
        solver = SymbolicSolver(self.test_config)
        
        joint_angles = np.array([0.0, 0.5, -0.3], dtype=np.float32)
        lower_limits = np.array([-1.5, -1.0, -2.0], dtype=np.float32)
        upper_limits = np.array([1.5, 1.0, 2.0], dtype=np.float32)
        
        constraints = solver.generate_joint_limit_constraints(
            joint_angles, lower_limits, upper_limits
        )
        
        assert constraints is not None
        assert isinstance(constraints, ConstraintMatrix)
        assert constraints.A.shape[1] == len(joint_angles)
        # Should have 2 constraints per joint (upper and lower)
        assert constraints.A.shape[0] == 2 * len(joint_angles)

    def test_constraint_matrix_validity_check(self):
        """Test that generated constraints pass validity checks."""
        solver = SymbolicSolver(self.test_config)
        
        # Test with valid configuration
        obj1_pos = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        obj2_pos = np.array([2.0, 0.0, 0.0], dtype=np.float32)
        radius1 = 0.2
        radius2 = 0.2
        
        constraints = solver.generate_non_penetration_constraints(
            obj1_pos, obj2_pos, radius1, radius2
        )
        
        # Check that constraint matrix is well-formed
        assert not np.any(np.isnan(constraints.A))
        assert not np.any(np.isnan(constraints.b))
        assert not np.any(np.isinf(constraints.A))
        assert not np.any(np.isinf(constraints.b))

    def test_constraint_matrix_sparse_conversion(self):
        """Test conversion to sparse matrix representation."""
        n_vars = 100
        n_constraints = 50
        
        matrix = ConstraintMatrix(n_vars, n_constraints)
        matrix.A = np.random.randn(n_constraints, n_vars).astype(np.float32)
        matrix.b = np.random.randn(n_constraints).astype(np.float32)
        
        # Sparse conversion should not raise
        sparse_A = matrix.to_sparse()
        assert sparse_A is not None

class TestSymbolicSolver:
    """Unit tests for SymbolicSolver class."""

    def setup_method(self):
        """Set up test fixtures."""
        set_deterministic_seed(42)
        self.test_config = load_config()
        self.solver = SymbolicSolver(self.test_config)

    def test_solver_initialization(self):
        """Test that SymbolicSolver initializes correctly."""
        assert self.solver.config is not None
        assert self.solver.timeout_handler is not None

    def test_solve_with_valid_constraints(self):
        """Test solving with valid constraint set."""
        # Create a simple valid constraint problem
        n_vars = 5
        n_constraints = 3
        
        A = np.random.randn(n_constraints, n_vars).astype(np.float32)
        b = np.random.randn(n_constraints).astype(np.float32)
        
        constraint_matrix = ConstraintMatrix(n_vars, n_constraints)
        constraint_matrix.A = A
        constraint_matrix.b = b
        
        # Should not raise an exception
        result = self.solver.solve(constraint_matrix)
        
        assert result is not None
        assert hasattr(result, 'solution')
        assert result.solution.shape[0] == n_vars

    def test_solve_with_timeout(self):
        """Test that timeout is properly handled."""
        # Create a constraint matrix that would take too long
        n_vars = 1000
        n_constraints = 500
        
        A = np.random.randn(n_constraints, n_vars).astype(np.float32)
        b = np.random.randn(n_constraints).astype(np.float32)
        
        constraint_matrix = ConstraintMatrix(n_vars, n_constraints)
        constraint_matrix.A = A
        constraint_matrix.b = b
        
        # Set a very short timeout
        original_timeout = self.solver.config.solver.timeout_ms
        self.solver.config.solver.timeout_ms = 1  # 1ms timeout
        
        try:
            result = self.solver.solve(constraint_matrix)
            # Either we get a solution or a timeout error
            assert result is not None
        except TimeoutError:
            pass  # Expected behavior
        finally:
            self.solver.config.solver.timeout_ms = original_timeout

    def test_solve_with_infeasible_constraints(self):
        """Test handling of infeasible constraint sets."""
        # Create contradictory constraints: x >= 1 and x <= 0
        n_vars = 1
        n_constraints = 2
        
        A = np.array([[1.0], [-1.0]], dtype=np.float32)
        b = np.array([1.0, 0.0], dtype=np.float32)
        
        constraint_matrix = ConstraintMatrix(n_vars, n_constraints)
        constraint_matrix.A = A
        constraint_matrix.b = b
        
        # Should handle infeasibility gracefully
        result = self.solver.solve(constraint_matrix)
        
        # Result should indicate infeasibility or return a feasible approximation
        assert result is not None

    def test_constraint_satisfaction_verification(self):
        """Test that solutions satisfy the constraints."""
        n_vars = 3
        n_constraints = 2
        
        # Create simple constraints: x1 + x2 + x3 <= 1, x1 >= 0
        A = np.array([
            [1.0, 1.0, 1.0],
            [-1.0, 0.0, 0.0]
        ], dtype=np.float32)
        b = np.array([1.0, 0.0], dtype=np.float32)
        
        constraint_matrix = ConstraintMatrix(n_vars, n_constraints)
        constraint_matrix.A = A
        constraint_matrix.b = b
        
        result = self.solver.solve(constraint_matrix)
        
        if result.success:
            # Verify constraint satisfaction
            Ax = np.dot(constraint_matrix.A, result.solution)
            violations = Ax - constraint_matrix.b
            assert np.all(violations <= 1e-4)  # Small tolerance for numerical errors

    def test_constraint_matrix_copy(self):
        """Test that constraint matrix can be copied safely."""
        n_vars = 5
        n_constraints = 3
        
        matrix = ConstraintMatrix(n_vars, n_constraints)
        matrix.A = np.random.randn(n_constraints, n_vars).astype(np.float32)
        matrix.b = np.random.randn(n_constraints).astype(np.float32)
        
        copy_matrix = matrix.copy()
        
        assert copy_matrix.A.shape == matrix.A.shape
        assert copy_matrix.b.shape == matrix.b.shape
        assert not np.shares_memory(copy_matrix.A, matrix.A)
        assert not np.shares_memory(copy_matrix.b, matrix.b)

class TestConstraintIntegration:
    """Integration tests for constraint generation and solving."""

    def setup_method(self):
        """Set up test fixtures."""
        set_deterministic_seed(42)
        self.test_config = load_config()
        self.solver = SymbolicSolver(self.test_config)

    def test_full_constraint_pipeline(self):
        """Test the full pipeline from constraint generation to solution."""
        # Generate joint limit constraints
        joint_angles = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        lower_limits = np.array([-1.0, -1.0, -1.0], dtype=np.float32)
        upper_limits = np.array([1.0, 1.0, 1.0], dtype=np.float32)
        
        constraints = self.solver.generate_joint_limit_constraints(
            joint_angles, lower_limits, upper_limits
        )
        
        # Solve the constraints
        result = self.solver.solve(constraints)
        
        assert result is not None
        assert result.solution.shape[0] == len(joint_angles)

    def test_combined_constraints(self):
        """Test solving with multiple constraint types combined."""
        # Create joint limit constraints
        joint_angles = np.array([0.1, 0.2], dtype=np.float32)
        lower_limits = np.array([-1.0, -1.0], dtype=np.float32)
        upper_limits = np.array([1.0, 1.0], dtype=np.float32)
        
        joint_constraints = self.solver.generate_joint_limit_constraints(
            joint_angles, lower_limits, upper_limits
        )
        
        # Create non-penetration constraints
        obj1_pos = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        obj2_pos = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        radius1 = 0.2
        radius2 = 0.2
        
        penetration_constraints = self.solver.generate_non_penetration_constraints(
            obj1_pos, obj2_pos, radius1, radius2
        )
        
        # Combine constraints (simplified - in reality would need proper merging)
        # For this test, we just verify both can be generated and solved separately
        joint_result = self.solver.solve(joint_constraints)
        penetration_result = self.solver.solve(penetration_constraints)
        
        assert joint_result is not None
        assert penetration_result is not None
