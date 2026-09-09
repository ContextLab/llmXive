"""
Refactored FTLE (Finite-Time Lyapunov Exponent) analysis module.
Improves readability and maintainability while preserving all functionality.
"""
import numpy as np
from typing import Tuple, List, Dict, Any, Optional
from dataclasses import dataclass, field
import logging
from pathlib import Path
from scipy.integrate import solve_ivp, odeint

from utils.stability import check_numerical_validity, check_boundedness
from config import get_full_config

logger = logging.getLogger(__name__)


@dataclass
class FTLEResult:
    """Container for FTLE computation results."""
    trial_id: int
    N: int
    sigma: float
    T: int
    lambda_ftle: float
    is_valid: bool = True
    error_message: Optional[str] = None
    convergence_info: Optional[Dict[str, Any]] = None

def compute_jacobian(state: np.ndarray, N: int, rho: float = 28.0, 
                    sigma_param: float = 10.0, beta: float = 8.0/3.0,
                    coupling_strength: float = 0.1) -> np.ndarray:
    """
    Compute the Jacobian matrix for coupled Lorenz system at a given state.
    
    Args:
        state: Current state vector [x1, y1, z1, x2, y2, z2, ...]
        N: Number of oscillators
        rho: Lorenz parameter rho
        sigma_param: Lorenz parameter sigma
        beta: Lorenz parameter beta
        coupling_strength: Coupling strength between oscillators
        
    Returns:
        Jacobian matrix of shape (3N, 3N)
    """
    dim = 3 * N
    jacobian = np.zeros((dim, dim))
    
    for i in range(N):
        idx = i * 3
        x, y, z = state[idx:idx+3]
        
        # Diagonal block (individual oscillator)
        jacobian[idx, idx] = -sigma_param
        jacobian[idx, idx+1] = sigma_param
        jacobian[idx+1, idx] = rho - z
        jacobian[idx+1, idx+1] = -1.0
        jacobian[idx+1, idx+2] = -x
        jacobian[idx+2, idx+1] = y
        jacobian[idx+2, idx+2] = -beta
        
        # Coupling terms (nearest neighbor)
        if i > 0:
            prev_idx = (i-1) * 3
            jacobian[idx, prev_idx] = coupling_strength
            jacobian[idx+1, prev_idx+1] = coupling_strength
            jacobian[idx+2, prev_idx+2] = coupling_strength
        
        if i < N - 1:
            next_idx = (i+1) * 3
            jacobian[idx, next_idx] = coupling_strength
            jacobian[idx+1, next_idx+1] = coupling_strength
            jacobian[idx+2, next_idx+2] = coupling_strength
    
    return jacobian

def propagate_tangent_vectors(jacobian: np.ndarray, tangent_matrix: np.ndarray,
                             dt: float) -> np.ndarray:
    """
    Propagate tangent vectors using linearized dynamics.
    
    Args:
        jacobian: Jacobian matrix at current state
        tangent_matrix: Matrix of tangent vectors (dim x dim)
        dt: Time step
        
    Returns:
        Updated tangent matrix
    """
    return tangent_matrix + dt @ (jacobian @ tangent_matrix)

def orthonormalize(tangent_matrix: np.ndarray) -> np.ndarray:
    """
    Perform QR decomposition to orthonormalize tangent vectors.
    
    Args:
        tangent_matrix: Matrix of tangent vectors
        
    Returns:
        Orthonormalized tangent matrix
    """
    Q, R = np.linalg.qr(tangent_matrix)
    
    # Ensure proper orientation (determinant = 1)
    for i in range(Q.shape[1]):
        if Q[:, i].dot(tangent_matrix[:, i]) < 0:
            Q[:, i] = -Q[:, i]
    
    return Q

def compute_ftle_single_trajectory(trajectory: np.ndarray, 
                                  baseline_lambda: float,
                                  window_size: int) -> Tuple[float, bool, Optional[str]]:
    """
    Compute FTLE for a single trajectory over a sliding window.
    
    Args:
        trajectory: State trajectory array (time_steps, 3N)
        baseline_lambda: Baseline Lyapunov exponent for comparison
        window_size: Size of the sliding window
        
    Returns:
        Tuple of (FTLE value, is_valid, error_message)
    """
    if trajectory.shape[0] < window_size + 10:
        return 0.0, False, "Trajectory too short for window size"
    
    dim = trajectory.shape[1]
    n_steps = trajectory.shape[0]
    
    # Initialize tangent vectors
    tangent_matrix = np.eye(dim)
    lyapunov_sum = 0.0
    
    dt = 0.01  # Time step
    
    for t in range(min(window_size, n_steps - 11)):
        state = trajectory[t]
        jacobian = compute_jacobian(state, dim // 3)
        
        # Propagate tangent vectors
        tangent_matrix = propagate_tangent_vectors(jacobian, tangent_matrix, dt)
        
        # Orthonormalize periodically
        if t % 10 == 0:
            tangent_matrix = orthonormalize(tangent_matrix)
        
        # Accumulate Lyapunov exponent estimate
        norms = np.linalg.norm(tangent_matrix, axis=0)
        lyapunov_sum += np.sum(np.log(np.maximum(norms, 1e-10)))
    
    ftle = lyapunov_sum / (window_size * dt * dim)
    
    # Validate result
    is_valid = check_numerical_validity(np.array([ftle]))
    error_msg = None if is_valid else "Invalid FTLE value computed"
    
    return ftle, is_valid, error_msg

def run_sliding_window_sweep(trajectory: np.ndarray, 
                            baseline_lambda: float,
                            window_sizes: List[int]) -> List[FTLEResult]:
    """
    Run FTLE computation across multiple window sizes.
    
    Args:
        trajectory: State trajectory array
        baseline_lambda: Baseline Lyapunov exponent
        window_sizes: List of window sizes to test
        
    Returns:
        List of FTLEResult objects
    """
    results = []
    N = trajectory.shape[1] // 3
    
    for window_size in window_sizes:
        ftle, is_valid, error_msg = compute_ftle_single_trajectory(
            trajectory, baseline_lambda, window_size
        )
        
        result = FTLEResult(
            trial_id=0,
            N=N,
            sigma=0.0,
            T=window_size,
            lambda_ftle=ftle,
            is_valid=is_valid,
            error_message=error_msg
        )
        results.append(result)
    
    return results

def compute_ftle_batch(trajectories: List[np.ndarray], 
                      baseline_lambda: float,
                      window_sizes: List[int],
                      trial_ids: List[int],
                      N: int,
                      sigma: float) -> List[FTLEResult]:
    """
    Compute FTLE for a batch of trajectories.
    
    Args:
        trajectories: List of trajectory arrays
        baseline_lambda: Baseline Lyapunov exponent
        window_sizes: List of window sizes
        trial_ids: Trial identifiers
        N: Number of oscillators
        sigma: Noise level
        
    Returns:
        List of FTLEResult objects
    """
    all_results = []
    
    for traj, trial_id in zip(trajectories, trial_ids):
        results = run_sliding_window_sweep(traj, baseline_lambda, window_sizes)
        
        # Update metadata
        for result in results:
            result.trial_id = trial_id
            result.N = N
            result.sigma = sigma
        
        all_results.extend(results)
    
    return all_results

def load_baseline_and_compute_ftle(baseline_path: Path, 
                                  trajectory_path: Path,
                                  window_sizes: List[int]) -> Optional[FTLEResult]:
    """
    Load baseline and trajectory, then compute FTLE.
    
    Args:
        baseline_path: Path to baseline JSON file
        trajectory_path: Path to trajectory CSV file
        window_sizes: List of window sizes to test
        
    Returns:
        FTLEResult or None if loading fails
    """
    try:
        import json
        with open(baseline_path, 'r') as f:
            baseline_data = json.load(f)
        
        baseline_lambda = baseline_data['lambda_max']
        
        # Load trajectory
        trajectory = np.loadtxt(trajectory_path, delimiter=',', skiprows=1)
        
        # Compute FTLE
        results = run_sliding_window_sweep(trajectory, baseline_lambda, window_sizes)
        return results[0] if results else None
        
    except Exception as e:
        logger.error(f"Failed to compute FTLE: {e}")
        return None

def save_ftle_results(results: List[FTLEResult], output_path: Path) -> None:
    """
    Save FTLE results to JSON file.
    
    Args:
        results: List of FTLEResult objects
        output_path: Output file path
    """
    import json
    
    data = [
        {
            'trial_id': r.trial_id,
            'N': r.N,
            'sigma': r.sigma,
            'T': r.T,
            'lambda_ftle': r.lambda_ftle,
            'is_valid': r.is_valid,
            'error_message': r.error_message
        }
        for r in results
    ]
    
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Saved {len(results)} FTLE results to {output_path}")

def main():
    """Main entry point for FTLE analysis module."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Compute FTLE for trajectories')
    parser.add_argument('--baseline', type=str, required=True, help='Baseline JSON path')
    parser.add_argument('--trajectory', type=str, required=True, help='Trajectory CSV path')
    parser.add_argument('--output', type=str, required=True, help='Output JSON path')
    parser.add_argument('--windows', type=int, nargs='+', default=[500, 1000, 5000],
                       help='Window sizes')
    
    args = parser.parse_args()
    
    result = load_baseline_and_compute_ftle(
        Path(args.baseline),
        Path(args.trajectory),
        args.windows
    )
    
    if result:
        save_ftle_results([result], Path(args.output))
    else:
        logger.error("FTLE computation failed")
