import numpy as np
from typing import Tuple, Dict, Any, Optional
from simulation.state import SimulationState
import logging

logger = logging.getLogger(__name__)

class SequentialSinkhornSolver:
    """
    Sequential Sinkhorn solver for autoregressive simulation.
    
    This solver maintains cumulative error state across steps and implements
    the core solver logic for the KVarN method.
    """
    
    def __init__(self, epsilon: float = 1e-6, max_iterations: int = 100, tolerance: float = 1e-4):
        """
        Initialize the Sequential Sinkhorn Solver.
        
        Args:
            epsilon: Epsilon floor for numerical stability.
            max_iterations: Maximum number of Sinkhorn iterations.
            tolerance: Convergence tolerance.
        """
        self.epsilon = epsilon
        self.max_iterations = max_iterations
        self.tolerance = tolerance
    
    def _compute_scaling_factor(self, matrix: np.ndarray) -> float:
        """
        Compute a single scaling factor for the given matrix using Sinkhorn iterations.
        
        Args:
            matrix: Input attention matrix (normalized).
            
        Returns:
            Scaling factor as a float.
        """
        # Ensure numerical stability
        matrix = np.clip(matrix, self.epsilon, 1.0)
        
        # Initialize scaling vectors
        n = matrix.shape[0]
        u = np.ones(n)
        v = np.ones(n)
        
        # Sinkhorn iterations
        for iteration in range(self.max_iterations):
            u_prev = u.copy()
            
            # Update u and v
            u = 1.0 / (matrix @ v + self.epsilon)
            v = 1.0 / (matrix.T @ u + self.epsilon)
            
            # Check convergence
            if np.max(np.abs(u - u_prev)) < self.tolerance:
                break
        
        # Compute scaling factor as the geometric mean of the scaling vectors
        scaling_factor = np.exp(np.mean(np.log(u + self.epsilon)))
        
        return float(scaling_factor)
    
    def _compute_kl_divergence(self, p: np.ndarray, q: np.ndarray) -> float:
        """
        Compute KL-divergence between two distributions.
        
        Args:
            p: First distribution (row-stochastic).
            q: Second distribution (row-stochastic).
            
        Returns:
            KL-divergence value.
        """
        # Ensure numerical stability
        p = np.clip(p, self.epsilon, 1.0)
        q = np.clip(q, self.epsilon, 1.0)
        
        # Normalize to ensure they are valid distributions
        p = p / (np.sum(p, axis=1, keepdims=True) + self.epsilon)
        q = q / (np.sum(q, axis=1, keepdims=True) + self.epsilon)
        
        # Compute KL-divergence
        kl = np.sum(p * np.log(p / q + self.epsilon))
        
        return float(kl)
    
    def solve_step(
        self,
        matrix: np.ndarray,
        prev_state: SimulationState
    ) -> Tuple[float, SimulationState]:
        """
        Solve one step of the sequential Sinkhorn process.
        
        Args:
            matrix: Input attention matrix for this step.
            prev_state: Previous simulation state.
            
        Returns:
            Tuple of (scaling_factor, new_state).
        """
        # Compute scaling factor
        scaling_factor = self._compute_scaling_factor(matrix)
        
        # Apply scaling to get quantized approximation
        # Simplified quantization for simulation purposes
        quantized_matrix = np.clip(matrix * scaling_factor, self.epsilon, 1.0)
        quantized_matrix = quantized_matrix / (np.sum(quantized_matrix, axis=1, keepdims=True) + self.epsilon)
        
        # Compute KL-divergence between original and quantized
        original_normalized = matrix / (np.sum(matrix, axis=1, keepdims=True) + self.epsilon)
        kl_div = self._compute_kl_divergence(original_normalized, quantized_matrix)
        
        # Update state
        new_accumulated_kl = prev_state.accumulated_kl + kl_div
        new_step_index = prev_state.step_index + 1
        new_trajectory = prev_state.full_trajectory + [kl_div]
        
        new_state = SimulationState(
            accumulated_kl=new_accumulated_kl,
            current_error_state={"kl_div": kl_div, "scaling_factor": scaling_factor},
            step_index=new_step_index,
            full_trajectory=new_trajectory
        )
        
        return scaling_factor, new_state

def run_sequential_simulation(
    matrices: np.ndarray,
    epsilon: float = 1e-6,
    seed: Optional[int] = None
) -> SimulationState:
    """
    Run a full sequential simulation over a list of matrices.
    
    Args:
        matrices: Array of attention matrices (N, 128, 128).
        epsilon: Epsilon floor for numerical stability.
        seed: Random seed for reproducibility.
        
    Returns:
        Final SimulationState after all steps.
    """
    if seed is not None:
        np.random.seed(seed)
    
    solver = SequentialSinkhornSolver(epsilon=epsilon)
    state = SimulationState(
        accumulated_kl=0.0,
        current_error_state={},
        step_index=0,
        full_trajectory=[]
    )
    
    for i, matrix in enumerate(matrices):
        _, state = solver.solve_step(matrix, state)
    
    return state
