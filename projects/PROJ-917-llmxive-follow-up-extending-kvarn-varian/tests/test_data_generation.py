"""
Comprehensive unit tests for the data generation pipeline, specifically focusing
on the SingleStepSinkhornSolver convergence behavior and edge cases.
"""
import pytest
import numpy as np
import sys
import os
from pathlib import Path

# Add code directory to path for imports
code_root = Path(__file__).parent.parent / "code"
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from data_generation.sinkhorn_solver import SingleStepSinkhornSolver, SinkhornNonConvergenceError
from data_generation.utils import apply_epsilon_floor, safe_log, safe_divide


class TestSingleStepSinkhornSolver:
    """
    Test suite for SingleStepSinkhornSolver focusing on:
    1. Convergence on standard matrices
    2. Handling of near-zero variance (edge case)
    3. Handling of non-convergence scenarios
    4. Numerical stability
    """

    def setup_method(self):
        """Initialize the solver for each test."""
        self.solver = SingleStepSinkhornSolver(max_iter=1000, tol=1e-9)

    def test_standard_convergence(self):
        """Test that the solver converges on a well-behaved random matrix."""
        np.random.seed(42)
        # Create a positive matrix with reasonable values
        matrix = np.random.rand(64, 64) + 0.1
        epsilon = 1e-5

        result = self.solver.solve(matrix, epsilon)

        # Check that we got a valid float result
        assert isinstance(result, float), "Solver should return a float"
        assert not np.isnan(result), "Result should not be NaN"
        assert not np.isinf(result), "Result should not be Inf"
        # The scaling factor for a normalized matrix should be positive
        assert result > 0, "Scaling factor should be positive"

    def test_near_zero_variance_handling(self):
        """
        Test behavior when input matrix has near-zero variance.
        This is a critical edge case for KVarN quantization.
        """
        # Create a matrix with very low variance (almost constant)
        base_value = 1.0
        noise = np.random.rand(64, 64) * 1e-10  # Extremely small noise
        matrix = np.full((64, 64), base_value) + noise

        epsilon = 1e-6

        # This should not raise an exception but handle gracefully
        result = self.solver.solve(matrix, epsilon)

        # Verify result is a valid number
        assert isinstance(result, float)
        assert not np.isnan(result)
        assert not np.isinf(result)

    def test_near_zero_variance_with_epsilon_floor(self):
        """
        Test that near-zero variance is handled correctly when epsilon floor is applied.
        """
        # Create a matrix with variance close to machine epsilon
        matrix = np.zeros((32, 32))
        matrix[0, 0] = 1e-20  # Tiny non-zero value

        epsilon = 1e-8
        result = self.solver.solve(matrix, epsilon)

        # Should handle without crashing
        assert isinstance(result, float)
        assert not np.isnan(result)

    def test_non_convergence_detection(self):
        """
        Test that the solver correctly detects and reports non-convergence.
        We force this by using a very small max_iter on a difficult matrix.
        """
        # Create a difficult matrix (highly skewed)
        matrix = np.random.rand(128, 128)
        matrix[0, :] = 1e-10  # Extremely small row
        matrix[:, 0] = 1e10   # Extremely large column

        # Use a very small max_iter to force non-convergence
        failing_solver = SingleStepSinkhornSolver(max_iter=2, tol=1e-9)

        # This should raise SinkhornNonConvergenceError
        with pytest.raises(SinkhornNonConvergenceError):
            failing_solver.solve(matrix, epsilon=1e-5)

    def test_non_convergence_with_ill_conditioned_matrix(self):
        """
        Test non-convergence on an ill-conditioned matrix with reasonable max_iter.
        """
        # Create a matrix that is likely to cause numerical instability
        np.random.seed(123)
        matrix = np.random.rand(64, 64)
        # Add a row of zeros to make it singular
        matrix[32, :] = 0.0

        # Use a solver that will struggle
        solver = SingleStepSinkhornSolver(max_iter=50, tol=1e-12)

        # Should raise error due to singularity
        with pytest.raises(SinkhornNonConvergenceError):
            solver.solve(matrix, epsilon=1e-6)

    def test_uniform_matrix(self):
        """Test with a uniform matrix (all elements equal)."""
        matrix = np.ones((32, 32))
        epsilon = 1e-5

        result = self.solver.solve(matrix, epsilon)

        assert isinstance(result, float)
        assert not np.isnan(result)
        # For a uniform matrix, the scaling factor should be close to 1.0
        # (allowing for numerical precision)
        assert 0.5 < result < 2.0, f"Uniform matrix scaling factor {result} out of expected range"

    def test_sparse_matrix(self):
        """Test with a sparse matrix (mostly zeros)."""
        matrix = np.random.rand(64, 64)
        matrix[matrix < 0.95] = 0.0  # Make it 95% sparse

        epsilon = 1e-5
        result = self.solver.solve(matrix, epsilon)

        assert isinstance(result, float)
        assert not np.isnan(result)
        assert not np.isinf(result)

    def test_extreme_values(self):
        """Test with extreme value ranges."""
        matrix = np.random.rand(32, 32)
        # Scale to extreme range
        matrix = matrix * 1e10 + 1e-10

        epsilon = 1e-8
        result = self.solver.solve(matrix, epsilon)

        assert isinstance(result, float)
        assert not np.isnan(result)
        assert not np.isinf(result)

    def test_very_small_epsilon(self):
        """Test convergence with very small epsilon."""
        matrix = np.random.rand(32, 32) + 0.1
        epsilon = 1e-12

        result = self.solver.solve(matrix, epsilon)

        assert isinstance(result, float)
        assert not np.isnan(result)
        # Small epsilon might take longer but should still converge
        assert result > 0

    def test_very_large_epsilon(self):
        """Test convergence with very large epsilon."""
        matrix = np.random.rand(32, 32) + 0.1
        epsilon = 1.0

        result = self.solver.solve(matrix, epsilon)

        assert isinstance(result, float)
        assert not np.isnan(result)
        assert result > 0


class TestEdgeCaseHelpers:
    """Tests for helper functions used in edge case handling."""

    def test_apply_epsilon_floor_zero_variance(self):
        """Test epsilon floor application on zero variance."""
        var = 0.0
        epsilon = 1e-6
        result = apply_epsilon_floor(var, epsilon)
        assert result == epsilon, "Zero variance should be floored to epsilon"

    def test_apply_epsilon_floor_negative_variance(self):
        """Test epsilon floor on negative variance (numerical error)."""
        var = -1e-15
        epsilon = 1e-6
        result = apply_epsilon_floor(var, epsilon)
        assert result == epsilon, "Negative variance should be floored to epsilon"

    def test_safe_divide_zero_denominator(self):
        """Test safe division by zero."""
        result = safe_divide(1.0, 0.0)
        assert np.isnan(result), "Division by zero should return NaN"

    def test_safe_log_negative(self):
        """Test safe log on negative number."""
        result = safe_log(-1.0)
        assert np.isnan(result), "Log of negative should return NaN"

    def test_safe_log_zero(self):
        """Test safe log on zero."""
        result = safe_log(0.0)
        assert np.isnan(result), "Log of zero should return NaN"


class TestSolverDeterminism:
    """Test that the solver produces deterministic results with fixed seeds."""

    def test_deterministic_results(self):
        """Verify same input produces same output."""
        np.random.seed(999)
        matrix = np.random.rand(32, 32) + 0.1
        epsilon = 1e-5

        solver1 = SingleStepSinkhornSolver(max_iter=100, tol=1e-9)
        solver2 = SingleStepSinkhornSolver(max_iter=100, tol=1e-9)

        result1 = solver1.solve(matrix, epsilon)
        result2 = solver2.solve(matrix, epsilon)

        assert result1 == result2, "Solver should be deterministic"

    def test_deterministic_across_runs(self):
        """Verify determinism across multiple independent runs."""
        np.random.seed(777)
        matrix = np.random.rand(32, 32) + 0.1
        epsilon = 1e-5

        results = []
        for _ in range(5):
            solver = SingleStepSinkhornSolver(max_iter=100, tol=1e-9)
            results.append(solver.solve(matrix, epsilon))

        # All results should be identical
        assert all(r == results[0] for r in results), "All runs should produce identical results"