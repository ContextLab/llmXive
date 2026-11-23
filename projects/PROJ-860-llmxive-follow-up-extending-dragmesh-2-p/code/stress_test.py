"""
Stress test script for VirtualTactileEstimator with noise injection.

This script validates the stability and accuracy of the estimator under
varying noise conditions, simulating sensor imperfections and extreme
friction scenarios as required by US2.

It generates synthetic torque/velocity pairs with controlled noise levels,
runs the estimator, and outputs statistical metrics (MAE, StdDev) to
data/generated/stress_test_results.json.
"""
import os
import sys
import json
import logging
import argparse
import time
import numpy as np
from typing import Tuple, List, Dict, Any

# Add parent directory to path for imports if running as script
if 'code' not in sys.path:
    code_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, code_dir)

from estimator import VirtualTactileEstimator
from logging_config import get_logger_for_module

logger = get_logger_for_module(__name__)

def generate_noisy_torque_velocity_pairs(
    base_friction: float,
    velocity_range: Tuple[float, float],
    noise_std: float,
    num_samples: int,
    rng: np.random.Generator
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate synthetic torque and velocity pairs with injected Gaussian noise.
    
    Args:
        base_friction: The underlying friction coefficient (ground truth).
        velocity_range: Tuple (min_vel, max_vel) for velocity sampling.
        noise_std: Standard deviation of the Gaussian noise to inject.
        num_samples: Number of samples to generate.
        rng: NumPy random generator for reproducibility.
    
    Returns:
        Tuple of (torque_array, velocity_array) with noise injected.
    """
    # Velocity is uniformly distributed in the given range
    velocities = rng.uniform(velocity_range[0], velocity_range[1], num_samples)
    
    # Theoretical torque = friction * velocity (simplified model for stress testing)
    # We add a small epsilon to velocity to avoid exact zero division in generation logic
    # if we were simulating the reverse, but here we generate torque directly.
    base_torques = base_friction * velocities
    
    # Inject Gaussian noise
    noise = rng.normal(0.0, noise_std, num_samples)
    noisy_torques = base_torques + noise
    
    # Ensure velocity doesn't become exactly zero if we were to use it as denominator later,
    # though the estimator handles it. We keep velocities as generated.
    return noisy_torques, velocities

def run_stress_test(
    noise_levels: List[float],
    friction_values: List[float],
    trials_per_config: int = 10,
    samples_per_trial: int = 100,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Execute the stress test suite across various noise levels and friction values.
    
    Args:
        noise_levels: List of noise standard deviations to test.
        friction_values: List of ground-truth friction coefficients to test.
        trials_per_config: Number of independent trials per (noise, friction) config.
        samples_per_trial: Number of samples per trial.
        seed: Random seed for reproducibility.
    
    Returns:
        Dictionary containing aggregated results and statistics.
    """
    rng = np.random.default_rng(seed)
    results = {
        "configs": [],
        "summary": {
            "mean_absolute_error_by_noise": {},
            "stability_variance_by_noise": {}
        }
    }
    
    logger.info(f"Starting stress test with {len(noise_levels)} noise levels and {len(friction_values)} friction values.")
    
    for noise_std in noise_levels:
        noise_results = []
        stability_vars = []
        
        for friction in friction_values:
            for trial_idx in range(trials_per_config):
                # Generate data
                torques, velocities = generate_noisy_torque_velocity_pairs(
                    base_friction=friction,
                    velocity_range=(0.1, 2.0), # Avoid zero velocity
                    noise_std=noise_std,
                    num_samples=samples_per_trial,
                    rng=rng
                )
                
                # Initialize estimator for this trial
                # Window=5, epsilon=1e-4 as per T005 specs
                estimator = VirtualTactileEstimator(window_size=5, epsilon=1e-4)
                
                est_values = []
                for t, v in zip(torques, velocities):
                    # Feed data point by point to simulate streaming
                    k_est = estimator.update(t, v)
                    if k_est is not None and np.isfinite(k_est):
                        est_values.append(k_est)
                
                if not est_values:
                    logger.warning(f"Trial {trial_idx} for friction={friction}, noise={noise_std} produced no valid estimates.")
                    continue
                
                # Calculate error metrics for this trial
                mean_est = np.mean(est_values)
                error = abs(mean_est - friction)
                noise_results.append(error)
                
                # Calculate variance as a stability metric
                if len(est_values) > 1:
                    stability_vars.append(np.var(est_values))
        
        # Aggregate results for this noise level
        if noise_results:
            results["summary"]["mean_absolute_error_by_noise"][str(noise_std)] = float(np.mean(noise_results))
            results["summary"]["stability_variance_by_noise"][str(noise_std)] = float(np.mean(stability_vars))
            logger.info(f"Noise Level {noise_std}: Mean MAE = {np.mean(noise_results):.4f}, Mean Variance = {np.mean(stability_vars):.4f}")
        else:
            logger.warning(f"No valid results for noise level {noise_std}")
    
    return results

def main():
    """Main entry point for the stress test script."""
    parser = argparse.ArgumentParser(description="Stress test VirtualTactileEstimator with noise injection.")
    parser.add_argument("--noise-levels", type=float, nargs="+", default=[0.0, 0.05, 0.1, 0.2, 0.5],
                        help="List of noise standard deviations to test.")
    parser.add_argument("--friction-values", type=float, nargs="+", default=[0.1, 0.5, 1.0, 1.5, 2.0],
                        help="List of ground-truth friction coefficients to test.")
    parser.add_argument("--trials", type=int, default=10, help="Trials per configuration.")
    parser.add_argument("--samples", type=int, default=100, help="Samples per trial.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    parser.add_argument("--output", type=str, default="data/generated/stress_test_results.json",
                        help="Path to save results JSON.")
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    output_dir = os.path.dirname(args.output)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    logger.info(f"Running stress test with seed={args.seed}")
    logger.info(f"Noise levels: {args.noise_levels}")
    logger.info(f"Friction values: {args.friction_values}")
    
    start_time = time.time()
    results = run_stress_test(
        noise_levels=args.noise_levels,
        friction_values=args.friction_values,
        trials_per_config=args.trials,
        samples_per_trial=args.samples,
        seed=args.seed
    )
    end_time = time.time()
    
    results["metadata"] = {
        "execution_time_seconds": end_time - start_time,
        "noise_levels_tested": args.noise_levels,
        "friction_values_tested": args.friction_values,
        "trials_per_config": args.trials,
        "samples_per_trial": args.samples,
        "seed": args.seed
    }
    
    # Write results to disk
    with open(args.output, "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Stress test completed. Results saved to {args.output}")
    print(f"Results written to {args.output}")

if __name__ == "__main__":
    # Initialize logging
    init_logger = logging.getLogger()
    if not init_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        init_logger.addHandler(handler)
        init_logger.setLevel(logging.INFO)
    
    main()