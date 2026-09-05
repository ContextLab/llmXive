"""
Single-step Sinkhorn solver for computing ground-truth scaling factors.

This module implements the SingleStepSinkhornSolver class used in User Story 1
to compute a single ground-truth scaling factor for an independent static matrix.
It does NOT maintain cumulative state across steps.
"""
import numpy as np
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class SinkhornNonConvergenceError(Exception):
    """Exception raised when the Sinkhorn algorithm fails to converge."""
    pass

class SingleStepSinkhornSolver:
    """
    Solver for computing a single ground-truth scaling factor using the 
    Sinkhorn-Knopp algorithm on a static attention matrix.
    
    This solver is designed for independent, single-step computation and does
    not maintain any cumulative state across calls.
    """
    
    def __init__(self, max_iterations: int = 1000, tolerance: float = 1e-6):
        """
        Initialize the solver.
        
        Args:
            max_iterations: Maximum number of Sinkhorn iterations.
            tolerance: Convergence tolerance for row/column sum differences.
        """
        self.max_iterations = max_iterations
        self.tolerance = tolerance
    
    def solve(self, matrix: np.ndarray, epsilon: float) -> float:
        """
        Compute a single ground-truth scaling factor for the input matrix.
        
        The algorithm normalizes the matrix to be doubly stochastic using
        the Sinkhorn-Knopp algorithm, then derives the scaling factor.
        
        Args:
            matrix: Input attention matrix (n x n).
            epsilon: Epsilon floor for numerical stability.
        
        Returns:
            A scalar scaling factor.
        
        Raises:
            SinkhornNonConvergenceError: If the algorithm fails to converge.
            ValueError: If the input matrix is invalid.
        """
        # Input validation
        if matrix is None:
            raise ValueError("Input matrix cannot be None")
        
        if not isinstance(matrix, np.ndarray):
            raise ValueError("Input must be a numpy array")
        
        if matrix.ndim != 2:
            raise ValueError("Input matrix must be 2-dimensional")
        
        if matrix.shape[0] != matrix.shape[1]:
            raise ValueError("Input matrix must be square")
        
        if matrix.shape[0] == 0:
            raise ValueError("Input matrix cannot be empty")
        
        # Apply epsilon floor to prevent division by zero
        matrix = np.maximum(matrix, epsilon)
        
        # Check for NaN or Inf after epsilon application
        if np.any(np.isnan(matrix)) or np.any(np.isinf(matrix)):
            logger.warning("Matrix contains NaN or Inf after epsilon application")
            raise SinkhornNonConvergenceError("Matrix contains NaN or Inf after epsilon application")
        
        n = matrix.shape[0]
        
        # Initialize scaling vectors
        u = np.ones(n)
        v = np.ones(n)
        
        # Sinkhorn-Knopp iterations
        for iteration in range(self.max_iterations):
            # Update u: row scaling factors
            row_sums = matrix @ v
            # Apply epsilon floor to prevent division by zero
            row_sums = np.maximum(row_sums, epsilon)
            u_new = 1.0 / row_sums
            
            # Update v: column scaling factors
            col_sums = matrix.T @ u_new
            # Apply epsilon floor to prevent division by zero
            col_sums = np.maximum(col_sums, epsilon)
            v_new = 1.0 / col_sums
            
            # Check for convergence
            u_change = np.max(np.abs(u_new - u))
            v_change = np.max(np.abs(v_new - v))
            
            u = u_new
            v = v_new
            
            if u_change < self.tolerance and v_change < self.tolerance:
                logger.debug(f"Sinkhorn converged in {iteration + 1} iterations")
                break
        else:
            # Did not converge within max_iterations
            logger.warning(
                f"Sinkhorn did not converge after {self.max_iterations} iterations. "
                f"Final u change: {u_change:.2e}, v change: {v_change:.2e}"
            )
            raise SinkhornNonConvergenceError(
                f"Sinkhorn did not converge after {self.max_iterations} iterations. "
                f"Final u change: {u_change:.2e}, v change: {v_change:.2e}"
            )
        
        # Compute the scaling factor
        # The scaling factor is derived from the product of the scaling vectors
        # s = (sum(u) * sum(v)) / n^2, normalized to be a single scalar
        sum_u = np.sum(u)
        sum_v = np.sum(v)
        
        # Ensure numerical stability in the final computation
        sum_u = np.maximum(sum_u, epsilon)
        sum_v = np.maximum(sum_v, epsilon)
        
        scaling_factor = (sum_u * sum_v) / (n * n)
        
        # Final check for validity
        if np.isnan(scaling_factor) or np.isinf(scaling_factor):
            logger.warning("Computed scaling factor is NaN or Inf")
            raise SinkhornNonConvergenceError("Computed scaling factor is NaN or Inf")
        
        return float(scaling_factor)
    
    def solve_batch(self, matrices: np.ndarray, epsilon: float) -> np.ndarray:
        """
        Solve for multiple matrices in a batch.
        
        Args:
            matrices: Stack of attention matrices (batch_size x n x n).
            epsilon: Epsilon floor for numerical stability.
        
        Returns:
            Array of scaling factors (batch_size,).
        
        Raises:
            SinkhornNonConvergenceError: If any matrix in the batch fails to converge.
        """
        if matrices.ndim != 3:
            raise ValueError("Batch input must be 3-dimensional (batch_size, n, n)")
        
        batch_size = matrices.shape[0]
        results = np.empty(batch_size, dtype=np.float64)
        
        for i in range(batch_size):
            try:
                results[i] = self.solve(matrices[i], epsilon)
            except SinkhornNonConvergenceError as e:
                logger.error(f"Batch item {i} failed to converge: {e}")
                raise  # Re-raise to fail loudly as per constraints
        
        return results