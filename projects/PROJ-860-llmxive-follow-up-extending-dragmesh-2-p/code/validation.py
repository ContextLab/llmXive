"""
Estimator Validation Module (T021, T022).

Provides tools to validate the VirtualTactileEstimator during training
by comparing estimated stiffness (k_est) against ground-truth friction
values.
"""

import numpy as np
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

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

def run_validation_suite(
    logs_dir: str,
    output_path: str
) -> None:
    """
    Run validation suite on a directory of episode logs.
    Aggregates validation results into a summary report.
    """
    import os
    import json
    import glob

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
    import argparse
    parser = argparse.ArgumentParser(description="Run estimator validation suite")
    parser.add_argument("--logs-dir", type=str, default="data/logs")
    parser.add_argument("--output", type=str, default="data/results/validation_summary.json")
    args = parser.parse_args()
    run_validation_suite(args.logs_dir, args.output)