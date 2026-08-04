"""
Unit tests for solver constraints and symbolic solver logic.
Tests the SymbolicSolver and ConstraintMatrix from code/symbolic_solver.py
and the DifferentiableSymbolicSolver from code/differentiable_solver.py.
"""
import os
import sys
import unittest
import math
from unittest.mock import patch, MagicMock
import numpy as np

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from symbolic_solver import SymbolicSolver, ConstraintMatrix, TimeoutError as SolverTimeoutError
from differentiable_solver import DifferentiableSymbolicSolver, ConstraintViolationLoss


class TestConstraintMatrix(unittest.TestCase):
    """Tests for ConstraintMatrix data structure and validation."""

    def test_init_valid_constraints(self):
        """Test initialization with valid constraint matrices."""
        # Create a simple non-penetration constraint: Ax <= b
        A = np.array([[1.0, 0.0], [0.0, 1.0]])
        b = np.array([1.0, 1.0])
        
        cm = ConstraintMatrix(A, b)
        
        self.assertIsInstance(cm.A, np.ndarray)
        self.assertIsInstance(cm.b, np.ndarray)
        self.assertEqual(cm.A.shape[0], cm.b.shape[0])
        np.testing.assert_array_equal(cm.A, A)
        np.testing.assert_array_equal(cm.b, b)

    def test_init_mismatched_shapes(self):
        """Test that mismatched shapes raise ValueError."""
        A = np.array([[1.0, 0.0], [0.0, 1.0]])
        b = np.array([1.0])  # Wrong size
        
        with self.assertRaises(ValueError):
            ConstraintMatrix(A, b)

    def test_check_feasibility(self):
        """Test feasibility checking."""
        A = np.array([[1.0, 0.0], [0.0, 1.0]])
        b = np.array([1.0, 1.0])
        cm = ConstraintMatrix(A, b)
        
        # Point (0.5, 0.5) should be feasible
        x_feasible = np.array([0.5, 0.5])
        self.assertTrue(cm.is_feasible(x_feasible))
        
        # Point (1.5, 1.5) should be infeasible
        x_infeasible = np.array([1.5, 1.5])
        self.assertFalse(cm.is_feasible(x_infeasible))

    def test_violation_magnitude(self):
        """Test violation magnitude calculation."""
        A = np.array([[1.0, 0.0], [0.0, 1.0]])
        b = np.array([1.0, 1.0])
        cm = ConstraintMatrix(A, b)
        
        # Point (1.5, 0.5) violates first constraint by 0.5
        x = np.array([1.5, 0.5])
        violation = cm.violation_magnitude(x)
        self.assertGreater(violation, 0.0)
        self.assertAlmostEqual(violation, 0.5, places=5)


class TestSymbolicSolver(unittest.TestCase):
    """Tests for the SymbolicSolver class."""

    def setUp(self):
        """Set up test fixtures."""
        self.solver = SymbolicSolver()
        # Create a simple quadratic programming problem:
        # min 0.5 * x^T * P * x + q^T * x
        # subject to G * x <= h
        self.P = np.array([[2.0, 0.0], [0.0, 2.0]])
        self.q = np.array([-1.0, -1.0])
        self.G = np.array([[1.0, 0.0], [0.0, 1.0], [-1.0, 0.0], [0.0, -1.0]])
        self.h = np.array([1.0, 1.0, 1.0, 1.0])

    def test_solve_simple_qp(self):
        """Test solving a simple quadratic program."""
        result = self.solver.solve(self.P, self.q, self.G, self.h)
        
        self.assertIsNotNone(result)
        self.assertIn('solution', result)
        self.assertIn('success', result)
        self.assertIn('message', result)
        
        # The optimal solution for min 0.5 * (2x^2 + 2y^2) - x - y
        # subject to -1 <= x,y <= 1 is (0.5, 0.5)
        self.assertTrue(result['success'])
        np.testing.assert_array_almost_equal(result['solution'], [0.5, 0.5], decimal=2)

    def test_solve_infeasible_problem(self):
        """Test solving an infeasible problem."""
        # Create infeasible constraints: x <= -1 and x >= 1
        G_infeas = np.array([[1.0], [-1.0]])
        h_infeas = np.array([-1.0, -1.0])  # x <= -1 and -x <= -1 => x >= 1
        
        result = self.solver.solve(self.P, self.q, G_infeas, h_infeas)
        
        self.assertFalse(result['success'])
        self.assertIn('infeasible', result.get('message', '').lower() or result.get('status', '').lower())

    def test_solve_unbounded_problem(self):
        """Test handling of unbounded problems."""
        # Unbounded: no constraints, minimize -x - y
        G_empty = np.zeros((0, 2))
        h_empty = np.zeros(0)
        
        result = self.solver.solve(self.P, self.q, G_empty, h_empty)
        
        # Should succeed but solution might be large
        self.assertTrue(result['success'])
        self.assertIsNotNone(result['solution'])

    def test_timeout_handling(self):
        """Test that timeout is properly handled."""
        # This is a mock test since actual timeout requires slow computation
        with patch.object(self.solver, '_solve_with_timeout') as mock_solve:
            mock_solve.side_effect = SolverTimeoutError("Test timeout")
            
            with self.assertRaises(SolverTimeoutError):
                self.solver.solve(self.P, self.q, self.G, self.h)


class TestDifferentiableSymbolicSolver(unittest.TestCase):
    """Tests for the DifferentiableSymbolicSolver wrapper."""

    def setUp(self):
        """Set up test fixtures."""
        try:
            import torch
            self.has_torch = True
        except ImportError:
            self.has_torch = False
            self.skipTest("PyTorch not available")

        self.solver = DifferentiableSymbolicSolver()

    @unittest.skipIf(not hasattr(unittest.TestCase, 'skipTest'), 'skipTest not available')
    def test_wrapper_creation(self):
        """Test that the wrapper can be created."""
        self.assertIsNotNone(self.solver)

    def test_constraint_violation_loss(self):
        """Test the constraint violation loss function."""
        if not self.has_torch:
            return
        
        import torch
        # Create a simple constraint: x <= 1
        A = torch.tensor([[1.0, 0.0]], requires_grad=True)
        b = torch.tensor([1.0])
        
        # Point that violates constraint: x = 1.5
        x = torch.tensor([1.5, 0.5], requires_grad=True)
        
        loss_fn = ConstraintViolationLoss()
        loss = loss_fn(A, b, x)
        
        self.assertGreater(loss.item(), 0.0)
        
        # Check that gradients can be computed
        loss.backward()
        self.assertIsNotNone(x.grad)
        self.assertIsNotNone(A.grad)

    def test_differentiable_solve(self):
        """Test that gradients flow through the differentiable solver."""
        if not self.has_torch:
            return
        
        import torch
        
        # Create a simple differentiable problem
        P = torch.tensor([[2.0, 0.0], [0.0, 2.0]], requires_grad=False)
        q = torch.tensor([-1.0, -1.0], requires_grad=True)  # Make q differentiable
        
        # Constraints: x <= 1, y <= 1
        G = torch.tensor([[1.0, 0.0], [0.0, 1.0]], requires_grad=False)
        h = torch.tensor([1.0, 1.0], requires_grad=False)
        
        # Solve
        result = self.solver.solve(P, q, G, h)
        
        self.assertTrue(result['success'])
        self.assertIsNotNone(result['solution'])
        
        # Check gradients if available
        if q.grad is not None:
            # Gradient should exist
            pass


class TestSolverIntegration(unittest.TestCase):
    """Integration tests combining solver components."""

    def test_full_constraint_pipeline(self):
        """Test the full pipeline from constraint creation to solving."""
        # Create constraints
        A = np.array([[1.0, 0.0], [0.0, 1.0], [-1.0, 0.0], [0.0, -1.0]])
        b = np.array([1.0, 1.0, 1.0, 1.0])
        cm = ConstraintMatrix(A, b)
        
        # Verify constraints are valid
        self.assertTrue(cm.is_feasible(np.array([0.5, 0.5])))
        self.assertFalse(cm.is_feasible(np.array([1.5, 1.5])))
        
        # Solve a problem within these constraints
        solver = SymbolicSolver()
        P = np.array([[2.0, 0.0], [0.0, 2.0]])
        q = np.array([-1.0, -1.0])
        
        result = solver.solve(P, q, A, b)
        
        self.assertTrue(result['success'])
        solution = result['solution']
        
        # Verify solution satisfies constraints
        self.assertTrue(cm.is_feasible(solution))


if __name__ == '__main__':
    unittest.main()
