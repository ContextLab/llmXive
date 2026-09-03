"""
Shadowing Lemma Check implementation for chaotic systems.

Validates that noisy trajectories still shadow a true orbit by checking
divergence rates against the clean baseline before FTLE calculation.
"""
import numpy as np
from typing import Tuple, Dict, Any, Optional
from dataclasses import dataclass
import logging
from pathlib import Path

from config import get_full_config
from utils.stability import check_numerical_validity, detect_divergence_rate
from analysis.baseline import (
    load_baseline_result, 
    NonChaoticSystemError, 
    BaselineConvergenceError,
    validate_and_gate_for_baseline
)
from data.loader import load_trajectory

logger = logging.getLogger(__name__)

@dataclass
class ShadowingResult:
    """Result of the shadowing lemma check."""
    is_shadowing: bool
    divergence_rate: float
    baseline_lambda_max: float
    deviation_ratio: float
    shadowing_tolerance: float
    message: str
    trajectory_id: str
    noise_level: float

class ShadowingCheckError(Exception):
    """Raised when shadowing check fails or cannot be performed."""
    pass

def compute_divergence_rate(
    clean_trajectory: np.ndarray,
    noisy_trajectory: np.ndarray,
    dt: float = 0.01
) -> float:
    """
    Compute the divergence rate between clean and noisy trajectories.
    
    The divergence rate is estimated by measuring the exponential growth
    of the separation between the two trajectories over time.
    
    Args:
        clean_trajectory: Clean (noise-free) trajectory of shape (T, N*D)
        noisy_trajectory: Noisy trajectory of shape (T, N*D)
        dt: Time step between trajectory points
        
    Returns:
        Estimated divergence rate (Lyapunov-like exponent)
    """
    if clean_trajectory.shape != noisy_trajectory.shape:
        raise ValueError(
            f"Trajectory shapes must match: "
            f"{clean_trajectory.shape} vs {noisy_trajectory.shape}"
        )
    
    # Compute separation at each time step
    separation = np.linalg.norm(noisy_trajectory - clean_trajectory, axis=1)
    
    # Filter out zero separations to avoid log(0)
    valid_mask = separation > 1e-15
    if not np.any(valid_mask):
        logger.warning("All separations are near-zero; using minimum threshold")
        separation[~valid_mask] = 1e-15
        valid_mask = np.ones_like(valid_mask, dtype=bool)
    
    # Compute log of separation
    log_separation = np.log(separation)
    
    # Linear regression on log_separation vs time to get divergence rate
    time = np.arange(len(log_separation)) * dt
    valid_time = time[valid_mask]
    valid_log_sep = log_separation[valid_mask]
    
    if len(valid_time) < 10:
        logger.warning("Too few valid points for divergence rate estimation")
        return 0.0
    
    # Fit linear model: log(separation) ≈ log(sep_0) + lambda * t
    coeffs = np.polyfit(valid_time, valid_log_sep, 1)
    divergence_rate = coeffs[0]  # Slope is the divergence rate
    
    return divergence_rate

def validate_shadowing_lemma(
    trajectory_id: str,
    noise_level: float,
    config: Dict[str, Any],
    data_dir: Optional[Path] = None,
    shadowing_tolerance: float = 0.1
) -> ShadowingResult:
    """
    Validate that a noisy trajectory shadows a true orbit.
    
    This function:
    1. Loads the clean and noisy trajectories
    2. Computes the divergence rate between them
    3. Compares against the asymptotic baseline
    4. Returns whether the shadowing lemma holds
    
    Args:
        trajectory_id: Identifier for the trajectory pair
        noise_level: Noise level (sigma) used for this trajectory
        config: Configuration dictionary with N, D, etc.
        data_dir: Directory containing trajectory files
        shadowing_tolerance: Maximum allowed deviation ratio for shadowing
        
    Returns:
        ShadowingResult with validation details
    """
    if data_dir is None:
        data_dir = Path(config.get('data_dir', 'data'))
    
    # Load baseline for this configuration
    N = config.get('N', 1)
    baseline_path = data_dir / 'processed' / f'baseline_{N}.json'
    
    try:
        baseline_data = load_baseline_result(baseline_path)
        baseline_lambda_max = baseline_data['lambda_max']
    except FileNotFoundError:
        raise ShadowingCheckError(
            f"Baseline file not found: {baseline_path}. "
            "Run baseline computation first."
        )
    except KeyError as e:
        raise ShadowingCheckError(
            f"Baseline file missing required key: {e}"
        )
    
    # Validate baseline convergence
    if 'error_estimate' in baseline_data:
        if baseline_data['error_estimate'] > 0.05:
            logger.warning(
                f"Baseline error estimate {baseline_data['error_estimate']:.4f} "
                "exceeds 5% threshold"
            )
    
    # Load trajectories
    clean_file = data_dir / 'raw' / f'trajectory_clean_{trajectory_id}.npz'
    noisy_file = data_dir / 'raw' / f'trajectory_noisy_{trajectory_id}_{noise_level:.4f}.npz'
    
    try:
        clean_data = load_trajectory(str(clean_file))
        noisy_data = load_trajectory(str(noisy_file))
    except FileNotFoundError as e:
        raise ShadowingCheckError(f"Trajectory file not found: {e}")
    
    # Extract trajectory arrays
    clean_traj = clean_data['trajectory']
    noisy_traj = noisy_data['trajectory']
    
    # Get time step from config
    dt = config.get('dt', 0.01)
    
    # Compute divergence rate
    divergence_rate = compute_divergence_rate(clean_traj, noisy_traj, dt)
    
    # Calculate deviation ratio
    # The shadowing lemma suggests divergence should be bounded by noise level
    # and the system's Lyapunov exponent
    if baseline_lambda_max > 0:
        deviation_ratio = abs(divergence_rate - baseline_lambda_max) / baseline_lambda_max
    else:
        deviation_ratio = float('inf') if divergence_rate != 0 else 0.0
    
    # Determine if shadowing holds
    # Shadowing holds if the divergence rate is within tolerance of the baseline
    is_shadowing = deviation_ratio <= shadowing_tolerance
    
    # Generate message
    if is_shadowing:
        message = (
            f"Shadowing lemma validated: divergence rate {divergence_rate:.6f} "
            f"is within {shadowing_tolerance*100:.1f}% of baseline {baseline_lambda_max:.6f}"
        )
    else:
        message = (
            f"Shadowing lemma FAILED: divergence rate {divergence_rate:.6f} "
            f"deviates {deviation_ratio*100:.1f}% from baseline {baseline_lambda_max:.6f}. "
            f"Noisy trajectory may not shadow a true orbit."
        )
    
    logger.info(message)
    
    return ShadowingResult(
        is_shadowing=is_shadowing,
        divergence_rate=divergence_rate,
        baseline_lambda_max=baseline_lambda_max,
        deviation_ratio=deviation_ratio,
        shadowing_tolerance=shadowing_tolerance,
        message=message,
        trajectory_id=trajectory_id,
        noise_level=noise_level
    )

def run_shadowing_check_batch(
    trajectory_ids: list,
    noise_levels: list,
    config: Dict[str, Any],
    data_dir: Optional[Path] = None,
    shadowing_tolerance: float = 0.1
) -> Dict[str, ShadowingResult]:
    """
    Run shadowing check on multiple trajectory pairs.
    
    Args:
        trajectory_ids: List of trajectory identifiers
        noise_levels: List of corresponding noise levels
        config: Configuration dictionary
        data_dir: Directory containing trajectory files
        shadowing_tolerance: Maximum allowed deviation ratio
        
    Returns:
        Dictionary mapping trajectory_id to ShadowingResult
    """
    results = {}
    
    for traj_id, noise in zip(trajectory_ids, noise_levels):
        try:
            result = validate_shadowing_lemma(
                trajectory_id=traj_id,
                noise_level=noise,
                config=config,
                data_dir=data_dir,
                shadowing_tolerance=shadowing_tolerance
            )
            results[traj_id] = result
        except Exception as e:
            logger.error(f"Shadowing check failed for {traj_id}: {e}")
            results[traj_id] = ShadowingResult(
                is_shadowing=False,
                divergence_rate=float('nan'),
                baseline_lambda_max=float('nan'),
                deviation_ratio=float('nan'),
                shadowing_tolerance=shadowing_tolerance,
                message=f"Error: {str(e)}",
                trajectory_id=traj_id,
                noise_level=noise
            )
    
    return results

def gate_for_ftle_calculation(
    shadowing_results: Dict[str, ShadowingResult],
    required_shadowing_rate: float = 0.8
) -> bool:
    """
    Gate FTLE calculation based on shadowing results.
    
    Args:
        shadowing_results: Dictionary of shadowing check results
        required_shadowing_rate: Minimum fraction of trajectories that must shadow
        
    Returns:
        True if FTLE calculation can proceed, False otherwise
        
    Raises:
        ShadowingCheckError: If shadowing rate is below threshold
    """
    if not shadowing_results:
        raise ShadowingCheckError("No shadowing results to evaluate")
    
    valid_count = sum(1 for r in shadowing_results.values() if r.is_shadowing)
    total_count = len(shadowing_results)
    shadowing_rate = valid_count / total_count if total_count > 0 else 0.0
    
    if shadowing_rate < required_shadowing_rate:
        raise ShadowingCheckError(
            f"Shadowing check failed: only {shadowing_rate*100:.1f}% of trajectories "
            f"shadow true orbits (required: {required_shadowing_rate*100:.1f}%). "
            "FTLE calculation cannot proceed reliably."
        )
    
    logger.info(
        f"Shadowing gate passed: {valid_count}/{total_count} trajectories "
        f"({shadowing_rate*100:.1f}%) shadow true orbits"
    )
    return True

def main():
    """Main entry point for shadowing check."""
    logging.basicConfig(level=logging.INFO)
    
    config = get_full_config()
    data_dir = Path(config.get('data_dir', 'data'))
    
    # Example: Run shadowing check for a specific trajectory
    # In practice, this would be called from main.py with proper parameters
    logger.info("Shadowing lemma check module loaded")
    logger.info("Use validate_shadowing_lemma() or run_shadowing_check_batch() to perform checks")
    logger.info("Use gate_for_ftle_calculation() to gate FTLE computation")

if __name__ == "__main__":
    main()
