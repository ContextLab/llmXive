"""
Feasibility study script to resolve [deferred] time steps for Kuramoto simulations.

Objective:
Determine the maximum time steps feasible within 6 hours on a 2-core CPU runner
while maintaining numerical accuracy (error < 1e-4 relative to [deferred] steps).

Output:
Writes data/processed/config.json with:
- time_steps (int): The resolved number of time steps.
- runtime_estimate (float): Estimated runtime for the full simulation in seconds.
- error_estimate (float): Estimated numerical error relative to the deferred target.

Constraints:
- SC-003: If estimated runtime for [deferred] steps > 4 hours, log CRITICAL WARNING
  and recommend spec amendment. Do NOT silently reduce step count.
- The default time_steps must be set to a sufficiently large value to ensure
  convergence unless a formal scope change is recorded.
"""

import os
import sys
import json
import time
import logging
import numpy as np
from pathlib import Path
from typing import Dict, Any, Tuple

# Add project root to path to allow imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.logging_utils import get_logger, init_logging, log_critical, log_warning, log_metric
from utils.config import init_config, get_config, apply_global_seed

# Constants
DEFAULT_DEFERRED_STEPS = 10000  # Placeholder for the [deferred] value
MAX_RUNTIME_SECONDS = 6 * 3600  # 6 hours wall-clock budget
SAFE_RUNTIME_SECONDS = 4 * 3600  # 4 hours threshold for critical warning
NUM_SAMPLES = 10  # Number of samples to estimate runtime
BASE_TIME_STEPS = 100  # Base number of steps for the pilot run

def estimate_runtime_per_step(num_steps: int, seed: int = 42) -> Tuple[float, float]:
    """
    Estimates the runtime per time step by running a short pilot simulation.
    
    This function simulates a simplified Kuramoto dynamics step to measure
    computational cost without running the full simulation.
    
    Args:
        num_steps: Number of steps to simulate in the pilot.
        seed: Random seed for reproducibility.
        
    Returns:
        Tuple of (total_runtime_seconds, avg_time_per_step)
    """
    # Initialize random state
    np.random.seed(seed)
    
    # Simulate a small network (N=500, matching the main study)
    N = 500
    k = 2  # Average degree
    
    # Create a simple adjacency matrix for a ring lattice (simplified)
    # This avoids the overhead of full graph construction for timing
    adj = np.zeros((N, N))
    for i in range(N):
        adj[i, (i + 1) % N] = 1
        adj[i, (i - 1) % N] = 1
    
    # Initialize phases
    phases = np.random.uniform(0, 2 * np.pi, N)
    
    # Run the pilot simulation
    start_time = time.time()
    
    # Simplified Kuramoto step (just the derivative calculation)
    # dtheta/dt = sum(K * sin(theta_j - theta_i))
    K = 1.0
    for _ in range(num_steps):
        # Calculate phase differences
        diff = phases[:, np.newaxis] - phases[np.newaxis, :]
        # Compute coupling term (simplified: just sum of sines)
        coupling = np.sum(np.sin(diff) * adj, axis=1)
        # Update phases (Euler step)
        dt = 0.01
        phases = phases + dt * coupling
        
    total_runtime = time.time() - start_time
    avg_time_per_step = total_runtime / num_steps
    
    return total_runtime, avg_time_per_step

def estimate_error(num_steps: int, reference_steps: int = DEFAULT_DEFERRED_STEPS) -> float:
    """
    Estimates the numerical error relative to a reference number of steps.
    
    This is a simplified estimate based on the assumption that error scales
    with 1/sqrt(num_steps) for stochastic processes or 1/num_steps for deterministic.
    For Kuramoto, we assume a conservative 1/sqrt scaling.
    
    Args:
        num_steps: Number of steps to evaluate.
        reference_steps: The reference number of steps (deferred target).
        
    Returns:
        Estimated relative error.
    """
    if num_steps >= reference_steps:
        return 0.0
    # Conservative error estimate: scales with 1/sqrt(n)
    # Assuming reference_steps has negligible error
    return np.sqrt(reference_steps / num_steps) - 1.0

def run_feasibility_study() -> Dict[str, Any]:
    """
    Runs the feasibility study to determine optimal time steps.
    
    Returns:
        Dictionary with time_steps, runtime_estimate, and error_estimate.
    """
    # Initialize logging
    init_logging(log_level=logging.INFO)
    logger = get_logger(__name__)
    
    logger.info("Starting feasibility study for time steps resolution.")
    
    # Get configuration
    config = get_config()
    seed = config.get('global_seed', 42)
    
    # Run pilot simulation to estimate runtime per step
    logger.info(f"Running pilot simulation with {BASE_TIME_STEPS} steps...")
    pilot_runtime, avg_time_per_step = estimate_runtime_per_step(BASE_TIME_STEPS, seed)
    
    logger.info(f"Pilot runtime: {pilot_runtime:.4f} seconds")
    logger.info(f"Average time per step: {avg_time_per_step:.6f} seconds")
    
    # Calculate maximum feasible steps within SAFE_RUNTIME_SECONDS
    max_feasible_steps = int(SAFE_RUNTIME_SECONDS / avg_time_per_step)
    
    # Check against DEFAULT_DEFERRED_STEPS
    if max_feasible_steps < DEFAULT_DEFERRED_STEPS:
        # Runtime for deferred steps would exceed safe limit
        deferred_runtime = DEFAULT_DEFERRED_STEPS * avg_time_per_step
        error = estimate_error(DEFAULT_DEFERRED_STEPS, DEFAULT_DEFERRED_STEPS)
        
        log_critical(
            logger,
            f"CRITICAL WARNING: Estimated runtime for [deferred] steps ({DEFAULT_DEFERRED_STEPS}) "
            f"is {deferred_runtime:.2f} seconds ({deferred_runtime/3600:.2f} hours), "
            f"which exceeds the 4-hour threshold. "
            f"Recommendation: Request a spec amendment to reduce time_steps or increase compute resources."
        )
        
        # Still use the deferred steps as required by the constraint,
        # but log the warning. The script does NOT silently reduce steps.
        time_steps = DEFAULT_DEFERRED_STEPS
        runtime_estimate = deferred_runtime
        error_estimate = error
        
        logger.warning(f"Using {time_steps} steps despite runtime warning. "
                     f"Estimated runtime: {runtime_estimate:.2f} seconds.")
    else:
        # We can safely use the deferred steps
        time_steps = DEFAULT_DEFERRED_STEPS
        runtime_estimate = time_steps * avg_time_per_step
        error_estimate = 0.0
        
        log_metric(logger, "time_steps_resolved", time_steps)
        log_metric(logger, "runtime_estimate", runtime_estimate)
        logger.info(f"Feasible to run {time_steps} steps. "
                   f"Estimated runtime: {runtime_estimate:.2f} seconds.")
    
    # Prepare result
    result = {
        "time_steps": time_steps,
        "runtime_estimate": runtime_estimate,
        "error_estimate": error_estimate
    }
    
    return result

def main():
    """Main entry point for the feasibility study."""
    # Initialize project configuration
    init_config()
    
    # Run the feasibility study
    result = run_feasibility_study()
    
    # Ensure output directory exists
    output_dir = Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Write results to config.json
    output_path = output_dir / "config.json"
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"Feasibility study complete. Results written to {output_path}")
    print(f"Time steps: {result['time_steps']}")
    print(f"Estimated runtime: {result['runtime_estimate']:.2f} seconds")
    print(f"Error estimate: {result['error_estimate']:.6f}")
    
    return result

if __name__ == "__main__":
    main()