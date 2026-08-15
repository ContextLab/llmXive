"""
Estimator Validation Module (T021, T022).

Provides tools to validate the VirtualTactileEstimator during training
by comparing estimated stiffness (k_est) against ground-truth friction
values.
"""

import os
import sys
import json
import glob
import argparse
import logging
import numpy as np
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

# Local imports from project API surface
from estimator import VirtualTactileEstimator
from environment import PhysicsEnvironment, create_cpu_environment
from seed_config import set_seeds
from logging_config import get_logger

@dataclass
class EstimatorValidationResult:
    """Container for validation metrics."""
    mae: float  # Mean Absolute Error between k_est and ground truth
    correlation: float  # Pearson correlation between k_est and ground truth
    stability_variance: float  # Variance of k_est over stable steps
    total_steps_validated: int

def calculate_stability_variance(k_est_history: List[float], window: int = 10) -> float:
    """
    Calculate the variance of k_est over a sliding window to assess stability.
    Returns the average variance across all windows.
    """
    if len(k_est_history) < window:
        return 0.0
    
    variances = []
    for i in range(len(k_est_history) - window + 1):
        window_data = k_est_history[i : i + window]
        variances.append(np.var(window_data))
    
    return float(np.mean(variances)) if variances else 0.0

def validate_estimator_during_episode(
    tracker: List[Dict[str, Any]],
    ground_truth_friction: float
) -> EstimatorValidationResult:
    """
    Validate estimator performance over a single episode.

    Args:
        tracker: List of step dictionaries containing 'k_est' and other metrics.
        ground_truth_friction: The known friction coefficient for the object.

    Returns:
        EstimatorValidationResult with calculated metrics.
    """
    if not tracker:
        return EstimatorValidationResult(
            mae=0.0, correlation=0.0, stability_variance=0.0, total_steps_validated=0
        )

    k_est_values = np.array([step["k_est"] for step in tracker])
    # Ground truth is constant per episode
    gt_values = np.full_like(k_est_values, ground_truth_friction, dtype=float)

    # Filter out steps where velocity was too low (stiction/noise)
    # We only validate steps where velocity > 0.01 to avoid division artifacts
    valid_mask = np.array([step["velocity"] > 0.01 for step in tracker])
    
    if np.sum(valid_mask) < 2:
        # Not enough valid data points for correlation
        return EstimatorValidationResult(
            mae=float(np.mean(np.abs(k_est_values - gt_values))),
            correlation=0.0,
            stability_variance=calculate_stability_variance(k_est_values.tolist()),
            total_steps_validated=len(tracker)
        )

    k_est_valid = k_est_values[valid_mask]
    gt_valid = gt_values[valid_mask]

    # Calculate MAE
    mae = float(np.mean(np.abs(k_est_valid - gt_valid)))

    # Calculate Pearson correlation
    if np.std(k_est_valid) > 1e-6:
        correlation = float(np.corrcoef(k_est_valid, gt_valid)[0, 1])
        if np.isnan(correlation):
            correlation = 0.0
    else:
        correlation = 0.0

    # Calculate stability variance
    stability_var = calculate_stability_variance(k_est_valid.tolist())

    return EstimatorValidationResult(
        mae=mae,
        correlation=correlation,
        stability_variance=stability_var,
        total_steps_validated=len(tracker)
    )

def run_validation_sweep(
    friction_range: tuple,
    num_trials: int,
    steps_per_episode: int,
    seed: int,
    output_path: str,
    logger: Optional[logging.Logger] = None
) -> Dict[str, Any]:
    """
    Execute a sweep of randomized trials to correlate k_est with ground-truth friction.
    
    Args:
        friction_range: Tuple (min_friction, max_friction) for uniform sampling.
        num_trials: Number of independent episodes to run.
        steps_per_episode: Simulation steps per episode.
        seed: Random seed for reproducibility.
        output_path: Path to save the CSV results.
        logger: Logger instance.
    
    Returns:
        Dictionary containing summary statistics (correlation, mae, etc.).
    """
    if logger is None:
        logger = get_logger("validation")
    
    set_seeds(seed)
    logger.info(f"Starting validation sweep: {num_trials} trials, friction range {friction_range}")
    
    results = []
    env = create_cpu_environment()
    estimator = VirtualTactileEstimator(window_size=5)
    
    min_f, max_f = friction_range
    
    # We need to store the mean k_est for each trial to calculate global correlation
    trial_data = []

    for i in range(num_trials):
        # Sample ground truth friction
        gt_friction = np.random.uniform(min_f, max_f)
        logger.debug(f"Trial {i+1}/{num_trials}: Ground Truth Friction = {gt_friction:.4f}")
        
        # Reset environment
        env.reset()
        estimator.reset()
        
        tracker = []
        
        # Simulate dragging motion
        for step in range(steps_per_episode):
            t = step * 0.01
            # Ensure velocity is positive and non-zero to avoid stiction issues in simulation
            velocity = 0.1 * np.sin(t) + 0.05 
            
            # Simulate torque based on friction: Torque ~ Friction * Constant + Noise
            noise = np.random.normal(0, 0.01)
            torque = gt_friction * 0.5 + noise 
            
            # Update estimator
            k_est = estimator.update(torque, velocity)
            
            tracker.append({
                "step": step,
                "torque": torque,
                "velocity": velocity,
                "k_est": k_est,
                "ground_truth": gt_friction
            })
        
        # Validate this episode
        val_result = validate_estimator_during_episode(tracker, gt_friction)
        
        # Calculate mean k_est for global correlation
        valid_k_est = [step["k_est"] for step in tracker if step["velocity"] > 0.01]
        mean_k_est = np.mean(valid_k_est) if valid_k_est else 0.0
        
        trial_data.append({
            "trial_id": i + 1,
            "ground_truth_friction": gt_friction,
            "mean_k_est": mean_k_est,
            "mae": val_result.mae,
            "correlation": val_result.correlation,
            "stability_variance": val_result.stability_variance,
            "steps_validated": val_result.total_steps_validated
        })
        
        results.append({
            "trial_id": i + 1,
            "ground_truth_friction": gt_friction,
            "mae": val_result.mae,
            "correlation": val_result.correlation,
            "stability_variance": val_result.stability_variance,
            "steps_validated": val_result.total_steps_validated
        })
        
        logger.info(f"Trial {i+1} complete: MAE={val_result.mae:.4f}, Corr={val_result.correlation:.4f}")
    
    # Calculate Global Correlation: Mean k_est vs Ground Truth
    global_x = [d["ground_truth_friction"] for d in trial_data]
    global_y = [d["mean_k_est"] for d in trial_data]
    
    if len(global_x) > 1 and np.std(global_x) > 1e-6 and np.std(global_y) > 1e-6:
        global_corr = float(np.corrcoef(global_x, global_y)[0, 1])
    else:
        global_corr = 0.0
    
    # Calculate Global MAE
    global_mae = 0.0
    if global_x:
        errors = [abs(y - x) for x, y in zip(global_x, global_y)]
        global_mae = float(np.mean(errors))
    
    summary = {
        "num_trials": num_trials,
        "friction_range": list(friction_range),
        "global_correlation": global_corr,
        "global_mae": global_mae,
        "results": results
    }
    
    # Write CSV
    import csv
    csv_path = output_path.replace(".json", ".csv")
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["trial_id", "ground_truth_friction", "mae", "correlation", "stability_variance", "steps_validated"])
        writer.writeheader()
        for r in results:
            writer.writerow(r)
    
    # Write JSON Summary
    with open(output_path, "w") as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Validation sweep complete. Global Correlation: {global_corr:.4f}, Global MAE: {global_mae:.4f}")
    logger.info(f"Results written to {csv_path} and {output_path}")
    
    return summary

def run_validation_suite(
    logs_dir: str,
    output_path: str
) -> None:
    """
    Run validation suite on a directory of episode logs.
    Aggregates validation results into a summary report.
    """
    log_files = glob.glob(os.path.join(logs_dir, "episode_*.json"))
    
    results = []
    for log_file in log_files:
        with open(log_file, "r") as f:
            log_data = json.load(f)
        
        if log_data.get("validation"):
            results.append({
                "file": os.path.basename(log_file),
                **log_data["validation"]
            })
    
    if results:
        avg_mae = np.mean([r["mae"] for r in results])
        avg_corr = np.mean([r["correlation"] for r in results])
        
        summary = {
            "total_episodes_validated": len(results),
            "average_mae": float(avg_mae),
            "average_correlation": float(avg_corr)
        }
        
        with open(output_path, "w") as f:
            json.dump(summary, f, indent=2)
        
        print(f"Validation Summary written to {output_path}")
    else:
        print("No validation data found in logs.")

if __name__ == "__main__":
    import pandas as pd
    parser = argparse.ArgumentParser(description="Run estimator validation sweep (T021)")
    parser.add_argument("--friction-min", type=float, default=0.0, help="Minimum friction coefficient")
    parser.add_argument("--friction-max", type=float, default=2.5, help="Maximum friction coefficient")
    parser.add_argument("--num-trials", type=int, default=50, help="Number of trials")
    parser.add_argument("--steps", type=int, default=100, help="Steps per episode")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--output", type=str, default="data/results/validation_sweep.json", help="Output JSON path")
    args = parser.parse_args()
    
    setup_logging = get_logger("validation")
    setup_logging.info("Starting T021 Validation Sweep")
    
    run_validation_sweep(
        friction_range=(args.friction_min, args.friction_max),
        num_trials=args.num_trials,
        steps_per_episode=args.steps,
        seed=args.seed,
        output_path=args.output,
        logger=setup_logging
    )
    print("T021 Validation Complete.")