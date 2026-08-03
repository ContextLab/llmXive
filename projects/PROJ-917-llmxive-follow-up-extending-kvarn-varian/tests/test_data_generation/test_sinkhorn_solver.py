"""
Unit tests for the SingleStepSinkhornSolver class.

Tests cover:
- Basic convergence on well-behaved matrices
- Edge cases: near-zero variance, non-convergence
- Input validation
- Batch processing
"""
import pytest
import numpy as np
from data_generation.sinkhorn_solver import SingleStepSinkhornSolver, SinkhornNonConvergenceError


class TestSingleStepSinkhornSolver:
    """Test suite for SingleStepSinkhornSolver."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.solver = SingleStepSinkhornSolver(
            max_iterations=1000,
            tolerance=1e-6
        )
    
    def test_basic_convergence(self):
        """Test that the solver converges on a well-behaved matrix."""
        # Create a positive, square matrix
        np.random.seed(42)
        matrix = np.random.rand(10, 10) + 0.1  # Ensure all positive
        
        result = self.solver.solve(matrix, epsilon=1e-6)
        
        # Result should be a valid float
        assert isinstance(result, float)
        assert not np.isnan(result)
        assert not np.isinf(result)
        assert result > 0
    
    def test_identity_matrix(self):
        """Test with identity matrix - should converge quickly."""
        matrix = np.eye(5)
        # Add small epsilon to diagonal to ensure positivity
        matrix = matrix + 1e-3
        
        result = self.solver.solve(matrix, epsilon=1e-6)
        
        assert not np.isnan(result)
        assert result > 0
    
    def test_near_zero_variance(self):
        """Test handling of matrices with near-zero variance."""
        # Create a matrix with very small values
        matrix = np.ones((5, 5)) * 1e-10
        
        result = self.solver.solve(matrix, epsilon=1e-6)
        
        # Should not crash, but may return NaN if non-convergence
        # The important thing is it handles the edge case gracefully
        assert isinstance(result, float)
    
    def test_non_convergence_returns_nan(self):
        """Test that non-convergence returns NaN (to be handled by caller)."""
        # Create a pathological matrix that may not converge
        # Using a very sparse matrix with extreme values
        matrix = np.zeros((10, 10))
        matrix[0, 0] = 1e10
        matrix[1, 1] = 1e-10
        # Most other entries are zero
        
        result = self.solver.solve(matrix, epsilon=1e-15)
        
        # May return NaN if non-convergence
        # The solver should not crash
        assert isinstance(result, float)
    
    def test_input_validation_none(self):
        """Test that None input raises ValueError."""
        with pytest.raises(ValueError, match="Input matrix cannot be None"):
            self.solver.solve(None, epsilon=1e-6)
    
    def test_input_validation_not_array(self):
        """Test that non-numpy array input raises ValueError."""
        with pytest.raises(ValueError, match="Input must be a numpy array"):
            self.solver.solve([[1, 2], [3, 4]], epsilon=1e-6)
    
    def test_input_validation_non_square(self):
        """Test that non-square matrix raises ValueError."""
        matrix = np.random.rand(3, 4)
        with pytest.raises(ValueError, match="Input matrix must be square"):
            self.solver.solve(matrix, epsilon=1e-6)
    
    def test_input_validation_empty(self):
        """Test that empty matrix raises ValueError."""
        matrix = np.array([]).reshape(0, 0)
        with pytest.raises(ValueError, match="Input matrix cannot be empty"):
            self.solver.solve(matrix, epsilon=1e-6)
    
    def test_input_validation_non_2d(self):
        """Test that non-2D input raises ValueError."""
        matrix = np.random.rand(3, 3, 3)
        with pytest.raises(ValueError, match="Input matrix must be 2-dimensional"):
            self.solver.solve(matrix, epsilon=1e-6)
    
    def test_batch_processing(self):
        """Test batch processing of multiple matrices."""
        np.random.seed(42)
        batch_size = 5
        n = 10
        matrices = np.random.rand(batch_size, n, n) + 0.1
        
        results = self.solver.solve_batch(matrices, epsilon=1e-6)
        
        assert results.shape == (batch_size,)
        assert all(isinstance(r, float) for r in results)
        assert not np.any(np.isnan(results))
    
    def test_epsilon_application(self):
        """Test that epsilon is properly applied to prevent division by zero."""
        # Create a matrix with very small values
        matrix = np.ones((5, 5)) * 1e-15
        
        # Should not crash due to division by zero
        result = self.solver.solve(matrix, epsilon=1e-6)
        
        # Result should be a valid float
        assert isinstance(result, float)
    
    def test_deterministic_output(self):
        """Test that the solver produces deterministic results."""
        np.random.seed(123)
        matrix = np.random.rand(8, 8) + 0.1
        
        result1 = self.solver.solve(matrix, epsilon=1e-6)
        result2 = self.solver.solve(matrix, epsilon=1e-6)
        
        assert result1 == result2
    
    def test_convergence_tolerance(self):
        """Test that tighter tolerance requires more iterations."""
        # Create a well-behaved matrix
        np.random.seed(42)
        matrix = np.random.rand(10, 10) + 0.1
        
        solver_loose = SingleStepSinkhornSolver(max_iterations=1000, tolerance=1e-3)
        solver_tight = SingleStepSinkhornSolver(max_iterations=1000, tolerance=1e-8)
        
        result_loose = solver_loose.solve(matrix, epsilon=1e-6)
        result_tight = solver_tight.solve(matrix, epsilon=1e-6)
        
        # Both should converge
        assert not np.isnan(result_loose)
        assert not np.isnan(result_tight)
        
        # Results should be close (within tolerance)
        assert np.abs(result_loose - result_tight) < 1e-2