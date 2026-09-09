"""
Finite-Time Lyapunov Exponent (FTLE) computation module.

Implements tangent-linear propagation algorithm with Jacobian evaluation
at noisy points, sliding window logic, and strict boundary checks.
"""
import numpy as np
from typing import Tuple, List, Dict, Any, Optional
from dataclasses import dataclass
import logging
from pathlib import Path
from scipy.integrate import solve_ivp, odeint
import json
import sys
import os

# Add parent to path for imports if running as script
if __name__ == "__main__" and str(Path(__file__).parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_full_config
from data.loader import load_trajectory
from analysis.baseline import load_baseline_result, NonChaoticSystemError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class FTLEResult:
    """Container for FTLE computation results."""
    trial_id: int
    N: int
    sigma: float
    T: int  # Window size
    lambda_ftle: float
    window_start_idx: int
    window_end_idx: int
    tangent_vector_norms: Optional[np.ndarray] = None
    convergence_info: Optional[Dict[str, Any]] = None

def compute_jacobian(state: np.ndarray, N: int, rho: float = 28.0, sigma_param: float = 10.0, beta: float = 8.0/3.0) -> np.ndarray:
    """
    Compute the Jacobian matrix for the coupled Lorenz system.
    
    Args:
        state: Current state vector of shape (3*N,)
        N: Number of oscillators
        rho: Lorenz parameter
        sigma_param: Lorenz parameter
        beta: Lorenz parameter
        
    Returns:
        Jacobian matrix of shape (3*N, 3*N)
    """
    dim = 3 * N
    J = np.zeros((dim, dim))
    
    for i in range(N):
        idx = 3 * i
        x, y, z = state[idx:idx+3]
        
        # Diagonal block (self dynamics)
        J[idx, idx] = -sigma_param
        J[idx, idx+1] = sigma_param
        J[idx+1, idx] = rho - z
        J[idx+1, idx+1] = -1.0
        J[idx+1, idx+2] = -x
        J[idx+2, idx+1] = y
        J[idx+2, idx+2] = -beta
        
        # Coupling terms (if coupled system)
        # Assuming nearest-neighbor coupling with strength 0.1
        coupling_strength = 0.1
        if i > 0:
            prev_idx = 3 * (i - 1)
            J[idx, prev_idx] = coupling_strength
            J[idx+1, prev_idx+1] = coupling_strength
            J[idx+2, prev_idx+2] = coupling_strength
        if i < N - 1:
            next_idx = 3 * (i + 1)
            J[idx, next_idx] = coupling_strength
            J[idx+1, next_idx+1] = coupling_strength
            J[idx+2, next_idx+2] = coupling_strength
            
    return J

def propagate_tangent_vectors(
    J_matrix: np.ndarray, 
    tangent_vectors: np.ndarray, 
    dt: float
) -> np.ndarray:
    """
    Propagate tangent vectors using the Jacobian.
    
    Args:
        J_matrix: Jacobian matrix
        tangent_vectors: Matrix of tangent vectors (n_vectors, dim)
        dt: Time step
        
    Returns:
        Propagated tangent vectors
    """
    # Linear propagation: v_new = (I + J*dt) @ v_old
    dim = J_matrix.shape[0]
    I = np.eye(dim)
    propagation_matrix = I + J_matrix * dt
    
    # Apply to each tangent vector
    return tangent_vectors @ propagation_matrix.T

def orthonormalize(vectors: np.ndarray) -> np.ndarray:
    """
    Apply Gram-Schmidt orthonormalization to tangent vectors.
    
    Args:
        vectors: Matrix of vectors (n_vectors, dim)
        
    Returns:
        Orthonormalized vectors
    """
    n_vectors, dim = vectors.shape
    orthonormal = np.zeros_like(vectors)
    
    for i in range(n_vectors):
        v = vectors[i].copy()
        for j in range(i):
            v -= np.dot(v, orthonormal[j]) * orthonormal[j]
        
        norm = np.linalg.norm(v)
        if norm > 1e-10:
            orthonormal[i] = v / norm
        else:
            # If vector collapses, reinitialize with random direction
            orthonormal[i] = np.random.randn(dim)
            orthonormal[i] /= np.linalg.norm(orthonormal[i])
            
    return orthonormal

def compute_ftle_single_trajectory(
    trajectory: np.ndarray,
    T: int,
    dt: float,
    N: int,
    baseline_lambda: float,
    trial_id: int = 0
) -> FTLEResult:
    """
    Compute FTLE for a single trajectory over a specific window.
    
    Args:
        trajectory: State trajectory of shape (n_steps, 3*N)
        T: Window size (number of steps)
        dt: Time step
        N: Number of oscillators
        baseline_lambda: Asymptotic baseline Lyapunov exponent
        trial_id: Identifier for the trial
        
    Returns:
        FTLEResult object
    """
    n_steps, dim = trajectory.shape
    
    # CRITICAL: Enforce strict boundary check to prevent propagation errors
    # The window must leave at least 10 steps of buffer at the end
    if T >= n_steps - 10:
        logger.error(
            f"FTLE computation blocked: Window size T={T} approaches "
            f"trajectory length {n_steps}. "
            f"Strict constraint T < total_length - 10 violated. "
            f"Required: T < {n_steps - 10}, Got: T={T}."
        )
        raise ValueError(
            f"Window size T={T} is too large for trajectory length {n_steps}. "
            f"Must satisfy T < total_length - 10 (i.e., T < {n_steps - 10}) "
            f"to allow for tangent vector propagation without boundary errors."
        )
    
    # Initialize tangent vectors (orthonormal basis)
    tangent_vectors = np.eye(dim)
    log_norms = []
    
    current_t = 0
    end_t = T
    
    # Propagate over the window
    while current_t < end_t:
        state = trajectory[current_t]
        
        # Compute Jacobian at current state
        J = compute_jacobian(state, N)
        
        # Propagate tangent vectors
        tangent_vectors = propagate_tangent_vectors(J, tangent_vectors, dt)
        
        # Orthonormalize to prevent numerical collapse
        tangent_vectors = orthonormalize(tangent_vectors)
        
        # Record norms for FTLE calculation
        # Sum of log norms of all vectors
        norms = np.linalg.norm(tangent_vectors, axis=1)
        log_norms.append(np.sum(np.log(np.maximum(norms, 1e-10))))
        
        current_t += 1
    
    # Compute FTLE: (1/T) * sum(log norms)
    total_log_norm = sum(log_norms)
    lambda_ftle = total_log_norm / (T * dt)
    
    return FTLEResult(
        trial_id=trial_id,
        N=N,
        sigma=0.0, # Will be updated by caller
        T=T,
        lambda_ftle=lambda_ftle,
        window_start_idx=0,
        window_end_idx=T,
        convergence_info={"baseline": baseline_lambda}
    )

def run_sliding_window_sweep(
    trajectory: np.ndarray,
    window_sizes: List[int],
    dt: float,
    N: int,
    baseline_lambda: float,
    trial_id: int = 0,
    sigma: float = 0.0
) -> List[FTLEResult]:
    """
    Run FTLE computation over multiple window sizes (sliding window sweep).
    
    Args:
        trajectory: State trajectory of shape (n_steps, 3*N)
        window_sizes: List of window sizes T to test
        dt: Time step
        N: Number of oscillators
        baseline_lambda: Asymptotic baseline Lyapunov exponent
        trial_id: Identifier for the trial
        sigma: Noise level for this trajectory
        
    Returns:
        List of FTLEResult objects
    """
    n_steps, dim = trajectory.shape
    results = []
    
    logger.info(f"Starting sliding window sweep for trial {trial_id}, N={N}, "
                f"trajectory length={n_steps}")
    
    for T in window_sizes:
        try:
            # CRITICAL: Enforce strict boundary check BEFORE computation
            if T >= n_steps - 10:
                logger.warning(
                    f"Skipping window size T={T} for trial {trial_id}: "
                    f"Violates strict constraint T < total_length - 10. "
                    f"Trajectory length is {n_steps}, max allowed T is {n_steps - 11}."
                )
                # Log the specific error condition as requested by T044
                continue
                
            result = compute_ftle_single_trajectory(
                trajectory, T, dt, N, baseline_lambda, trial_id
            )
            result.sigma = sigma # Update noise level
            results.append(result)
            logger.info(f"  T={T}: lambda_ftle={result.lambda_ftle:.6f}")
            
        except ValueError as e:
            # This handles the specific T044 constraint violation
            logger.error(f"Window constraint error for T={T}: {e}")
            continue
        except Exception as e:
            logger.error(f"Unexpected error during FTLE computation for T={T}: {e}")
            continue
    
    return results

def compute_ftle_batch(
    trajectories: List[np.ndarray],
    window_sizes: List[int],
    dt: float,
    N: int,
    baseline_lambda: float,
    trial_ids: List[int],
    sigmas: List[float]
) -> List[FTLEResult]:
    """
    Compute FTLE for a batch of trajectories.
    
    Args:
        trajectories: List of trajectory arrays
        window_sizes: List of window sizes
        dt: Time step
        N: Number of oscillators
        baseline_lambda: Baseline Lyapunov exponent
        trial_ids: List of trial identifiers
        sigmas: List of noise levels
        
    Returns:
        List of FTLEResult objects
    """
    all_results = []
    
    for i, traj in enumerate(trajectories):
        results = run_sliding_window_sweep(
            traj, window_sizes, dt, N, baseline_lambda, 
            trial_ids[i], sigmas[i]
        )
        all_results.extend(results)
        
    return all_results

def load_baseline_and_compute_ftle(
    trajectory_path: str,
    baseline_path: str,
    window_sizes: List[int],
    dt: float,
    trial_id: int,
    sigma: float
) -> List[FTLEResult]:
    """
    Load baseline and trajectory, then compute FTLE.
    
    Args:
        trajectory_path: Path to trajectory CSV
        baseline_path: Path to baseline JSON
        window_sizes: List of window sizes
        dt: Time step
        trial_id: Trial identifier
        sigma: Noise level
        
    Returns:
        List of FTLEResult objects
    """
    # Load baseline
    try:
        baseline_data = load_baseline_result(baseline_path)
        baseline_lambda = baseline_data['lambda_max']
        logger.info(f"Loaded baseline lambda_max={baseline_lambda:.6f} from {baseline_path}")
    except Exception as e:
        logger.error(f"Failed to load baseline from {baseline_path}: {e}")
        raise
        
    # Load trajectory
    try:
        trajectory = load_trajectory(trajectory_path)
        logger.info(f"Loaded trajectory of shape {trajectory.shape} from {trajectory_path}")
    except Exception as e:
        logger.error(f"Failed to load trajectory from {trajectory_path}: {e}")
        raise
        
    # Compute FTLE
    return run_sliding_window_sweep(
        trajectory, window_sizes, dt, 
        trajectory.shape[1] // 3, baseline_lambda, trial_id, sigma
    )

def save_ftle_results(results: List[FTLEResult], output_path: str) -> None:
    """
    Save FTLE results to JSON.
    
    Args:
        results: List of FTLEResult objects
        output_path: Path to output JSON file
    """
    data = []
    for r in results:
        data.append({
            "trial_id": r.trial_id,
            "N": r.N,
            "sigma": r.sigma,
            "T": r.T,
            "lambda_ftle": r.lambda_ftle,
            "window_start_idx": r.window_start_idx,
            "window_end_idx": r.window_end_idx
        })
        
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
        
    logger.info(f"Saved {len(data)} FTLE results to {output_path}")

def main():
    """Main entry point for FTLE analysis."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Compute FTLE for chaotic trajectories")
    parser.add_argument("--trajectory", type=str, required=True, help="Path to trajectory CSV")
    parser.add_argument("--baseline", type=str, required=True, help="Path to baseline JSON")
    parser.add_argument("--output", type=str, required=True, help="Path to output JSON")
    parser.add_argument("--dt", type=float, default=0.01, help="Time step")
    parser.add_argument("--trial-id", type=int, default=0, help="Trial ID")
    parser.add_argument("--sigma", type=float, default=0.0, help="Noise level")
    
    args = parser.parse_args()
    
    # Default window sizes as per T023
    window_sizes = [500, 1000, 5000]
    
    results = load_baseline_and_compute_ftle(
        args.trajectory, args.baseline, window_sizes, 
        args.dt, args.trial_id, args.sigma
    )
    
    save_ftle_results(results, args.output)

if __name__ == "__main__":
    main()