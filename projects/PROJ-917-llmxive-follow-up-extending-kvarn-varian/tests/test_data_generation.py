"""
Unit tests for data generation utilities, specifically focusing on:
1. Epsilon floor handling (apply_epsilon_floor)
2. Moment extraction logic (mean, variance) as per Spec FR-002
3. SingleStepSinkhornSolver convergence and edge cases (T011)
"""
import pytest
import numpy as np
from data_generation.utils import apply_epsilon_floor, safe_log, safe_divide, check_numerical_stability
from data_generation.sinkhorn_solver import SingleStepSinkhornSolver

class TestSinkhornSolverEdgeCases:
    """Tests for SingleStepSinkhornSolver convergence and edge cases (T011)."""
    
    def test_solver_near_zero_variance_raises(self):
        """
        Verify that the solver handles near-zero variance by raising a convergence error.
        According to T016 requirements, non-convergence must be handled by raising
        a specific exception or returning NaN. We test for the exception path.
        """
        solver = SingleStepSinkhornSolver()
        
        # Create a matrix with near-zero variance (constant values)
        # This should cause the Sinkhorn iterations to fail to converge
        # or produce numerical instability.
        matrix = np.ones((10, 10)) * 5.0
        
        # Add tiny noise to avoid exact singularity but keep variance near zero
        matrix += np.random.normal(0, 1e-12, (10, 10))
        
        epsilon = 1e-6
        
        # The solver should raise a ConvergenceError or similar
        # We expect this to fail because variance is too low for stable scaling
        with pytest.raises((RuntimeError, ValueError, ZeroDivisionError)):
            solver.solve(matrix, epsilon)
    
    def test_solver_non_convergence_raises(self):
        """
        Verify that the solver handles non-convergence by raising an exception.
        We simulate this by using a matrix that is known to be ill-conditioned
        for the Sinkhorn algorithm (e.g., extreme sparsity with zeros).
        """
        solver = SingleStepSinkhornSolver()
        
        # Create a matrix with extreme sparsity (many zeros)
        # This can cause the Sinkhorn algorithm to fail to converge
        matrix = np.zeros((10, 10))
        matrix[0, 0] = 1.0  # Only one non-zero element
        
        epsilon = 1e-6
        
        # This should raise an exception due to non-convergence
        with pytest.raises((RuntimeError, ValueError, ZeroDivisionError)):
            solver.solve(matrix, epsilon)
    
    def test_solver_normal_convergence(self):
        """
        Verify that the solver converges for a well-conditioned matrix.
        This is the happy path to ensure the solver works correctly.
        """
        solver = SingleStepSinkhornSolver()
        
        # Create a well-conditioned matrix with reasonable variance
        np.random.seed(42)
        matrix = np.random.rand(10, 10)
        matrix = matrix + matrix.T  # Make it symmetric for stability
        
        epsilon = 1e-6
        
        # This should converge without raising an exception
        result = solver.solve(matrix, epsilon)
        
        # The result should be a finite scalar
        assert isinstance(result, float)
        assert np.isfinite(result)
        assert result > 0
    
    def test_solver_very_small_epsilon(self):
        """
        Verify behavior with a very small epsilon (numerical stress test).
        """
        solver = SingleStepSinkhornSolver()
        
        matrix = np.random.rand(10, 10)
        matrix = matrix + matrix.T
        
        epsilon = 1e-12
        
        # Should still converge for a well-conditioned matrix
        result = solver.solve(matrix, epsilon)
        
        assert np.isfinite(result)
    
    def test_solver_large_matrix(self):
        """
        Verify the solver handles a larger matrix (e.g., 128x128 as per spec).
        """
        solver = SingleStepSinkhornSolver()
        
        np.random.seed(123)
        matrix = np.random.rand(128, 128)
        matrix = matrix + matrix.T
        
        epsilon = 1e-6
        
        result = solver.solve(matrix, epsilon)
        
        assert np.isfinite(result)
        assert result > 0

class TestEpsilonFloor:
    """Tests for the apply_epsilon_floor function."""

    def test_apply_epsilon_floor_positive_value(self):
        """Verify that a value larger than epsilon is returned unchanged."""
        value = 1.0
        epsilon = 1e-6
        result = apply_epsilon_floor(value, epsilon)
        assert result == value

    def test_apply_epsilon_floor_below_epsilon(self):
        """Verify that a value smaller than epsilon is clamped to epsilon."""
        value = 1e-9
        epsilon = 1e-6
        result = apply_epsilon_floor(value, epsilon)
        assert result == epsilon

    def test_apply_epsilon_floor_zero(self):
        """Verify that zero is clamped to epsilon."""
        value = 0.0
        epsilon = 1e-6
        result = apply_epsilon_floor(value, epsilon)
        assert result == epsilon

    def test_apply_epsilon_floor_negative_value(self):
        """Verify that negative values are clamped to epsilon."""
        value = -5.0
        epsilon = 1e-6
        result = apply_epsilon_floor(value, epsilon)
        assert result == epsilon

    def test_apply_epsilon_floor_exact_epsilon(self):
        """Verify that a value exactly equal to epsilon is returned."""
        value = 1e-6
        epsilon = 1e-6
        result = apply_epsilon_floor(value, epsilon)
        assert result == epsilon


class TestMomentExtraction:
    """Tests for moment extraction logic (mean and variance) as per Spec FR-002."""

    def test_extract_mean_scalar(self):
        """Verify mean extraction from a simple 1D array."""
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        expected_mean = 3.0
        computed_mean = np.mean(data)
        assert np.isclose(computed_mean, expected_mean)

    def test_extract_mean_2d_array(self):
        """Verify mean extraction from a 2D array (flattened)."""
        data = np.array([[1.0, 2.0], [3.0, 4.0]])
        expected_mean = 2.5
        computed_mean = np.mean(data)
        assert np.isclose(computed_mean, expected_mean)

    def test_extract_variance_scalar(self):
        """Verify variance extraction from a simple 1D array."""
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        # Population variance (ddof=0)
        expected_var = 2.0
        computed_var = np.var(data, ddof=0)
        assert np.isclose(computed_var, expected_var)

    def test_extract_variance_with_epsilon_floor(self):
        """Verify that variance extraction handles near-zero variance correctly with epsilon floor."""
        # Create data with very small variance
        base = np.ones(100) * 5.0
        data = base + np.random.normal(0, 1e-10, 100)
        
        raw_var = np.var(data, ddof=0)
        # Apply epsilon floor manually to simulate the logic used in production
        epsilon = 1e-6
        clamped_var = apply_epsilon_floor(raw_var, epsilon)
        
        # The result should be at least epsilon if raw_var is very small
        assert clamped_var >= epsilon

    def test_moment_extraction_stability(self):
        """Verify that moment extraction is stable for constant arrays."""
        data = np.ones(100) * 5.0
        mean = np.mean(data)
        var = np.var(data, ddof=0)
        
        assert np.isclose(mean, 5.0)
        # Variance of constant is 0, which should be handled by epsilon floor in production
        assert var == 0.0

    def test_moment_extraction_with_outliers(self):
        """Verify moment extraction handles arrays with outliers."""
        data = np.array([1.0, 2.0, 3.0, 100.0])
        mean = np.mean(data)
        var = np.var(data, ddof=0)
        
        expected_mean = 26.5
        expected_var = 1830.75
        
        assert np.isclose(mean, expected_mean)
        assert np.isclose(var, expected_var)


class TestNumericalStabilityHelpers:
    """Additional tests for related numerical stability functions."""

    def test_safe_log_positive(self):
        """Verify safe_log works for positive values."""
        assert safe_log(1.0) == 0.0
        assert np.isclose(safe_log(np.e), 1.0)

    def test_safe_log_zero(self):
        """Verify safe_log handles zero by returning -inf or a safe value."""
        result = safe_log(0.0)
        # Depending on implementation, this might be -inf or a large negative number
        assert result <= 0.0

    def test_safe_divide_normal(self):
        """Verify safe_divide works for normal division."""
        assert safe_divide(1.0, 2.0) == 0.5

    def test_safe_divide_zero_denominator(self):
        """Verify safe_divide handles zero denominator."""
        result = safe_divide(1.0, 0.0)
        # Should return 0.0 or raise a specific error, depending on implementation
        # Assuming it returns 0.0 or a safe default
        assert result == 0.0

    def test_check_numerical_stability_no_issues(self):
        """Verify check_numerical_stability returns True for clean data."""
        data = np.array([1.0, 2.0, 3.0])
        assert check_numerical_stability(data)

    def test_check_numerical_stability_nan(self):
        """Verify check_numerical_stability detects NaN."""
        data = np.array([1.0, np.nan, 3.0])
        assert not check_numerical_stability(data)

    def test_check_numerical_stability_inf(self):
        """Verify check_numerical_stability detects Inf."""
        data = np.array([1.0, np.inf, 3.0])
        assert not check_numerical_stability(data)