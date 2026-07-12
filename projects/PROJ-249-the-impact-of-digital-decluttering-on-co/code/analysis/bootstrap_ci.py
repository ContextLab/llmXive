import os
import json
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import numpy as np
from utils.random_seed import get_rng, set_global_seed

@dataclass
class BootstrapResult:
    metric: str
    mean_change: float
    ci_lower: float
    ci_upper: float
    p_value: float
    n_resamples: int
    convergence: bool

def calculate_bootstrap_ci(
    baseline_values: List[float],
    post_values: List[float],
    n_resamples: int = 10000,
    confidence_level: float = 0.95,
    seed: Optional[int] = None
) -> BootstrapResult:
    """
    Calculate bootstrapped confidence interval for the mean difference.
    
    Uses vectorized operations for performance optimization.
    
    Args:
        baseline_values: List of baseline measurements
        post_values: List of post-intervention measurements
        n_resamples: Number of bootstrap resamples (default 10,000)
        confidence_level: Confidence level for CI (default 0.95)
        seed: Random seed for reproducibility
        
    Returns:
        BootstrapResult with mean change, CI bounds, and p-value
    """
    if len(baseline_values) != len(post_values):
        raise ValueError("Baseline and post values must have the same length")
    
    if len(baseline_values) == 0:
        raise ValueError("Input lists cannot be empty")
        
    if seed is not None:
        set_global_seed(seed)
    rng = get_rng()
    
    # Convert to numpy arrays for vectorized operations
    baseline_arr = np.array(baseline_values)
    post_arr = np.array(post_values)
    
    # Calculate observed mean difference
    observed_diff = np.mean(post_arr) - np.mean(baseline_arr)
    
    # Vectorized bootstrap resampling
    n = len(baseline_arr)
    
    # Generate all resample indices at once (n_resamples x n)
    # This is the key optimization: avoid Python loop
    resample_indices = rng.integers(0, n, size=(n_resamples, n))
    
    # Vectorized resampling: (n_resamples, n) x (n,) -> (n_resamples, n)
    # Use advanced indexing to select values for each resample
    resampled_baseline = baseline_arr[resample_indices]
    resampled_post = post_arr[resample_indices]
    
    # Calculate mean difference for all resamples at once
    resampled_diffs = np.mean(resampled_post, axis=1) - np.mean(resampled_baseline, axis=1)
    
    # Calculate confidence interval using percentiles
    alpha = 1 - confidence_level
    ci_lower = np.percentile(resampled_diffs, 100 * alpha / 2)
    ci_upper = np.percentile(resampled_diffs, 100 * (1 - alpha / 2))
    
    # Calculate two-tailed p-value
    # Count how many resampled diffs are as extreme or more extreme than observed
    # under the null hypothesis that mean difference is 0
    # We use the observed mean difference as the reference
    mean_resampled_diff = np.mean(resampled_diffs)
    centered_diffs = resampled_diffs - mean_resampled_diff
    
    # Two-tailed p-value: proportion of resampled diffs with |diff| >= |observed_diff - mean_resampled|
    extreme_count = np.sum(np.abs(centered_diffs) >= np.abs(observed_diff - mean_resampled_diff))
    p_value = extreme_count / n_resamples
    
    # Check for convergence (all resamples should have finite values)
    convergence = np.all(np.isfinite(resampled_diffs))
    
    return BootstrapResult(
        metric="",  # Will be set by caller
        mean_change=observed_diff,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        p_value=p_value,
        n_resamples=n_resamples,
        convergence=convergence
    )

def run_bootstrap_analysis(
    data: Dict[str, List[float]],
    n_resamples: int = 10000,
    confidence_level: float = 0.95,
    seed: Optional[int] = None
) -> Dict[str, BootstrapResult]:
    """
    Run bootstrap analysis for multiple metrics.
    
    Args:
        data: Dictionary mapping metric names to dict with 'baseline' and 'post' lists
        n_resamples: Number of bootstrap resamples
        confidence_level: Confidence level for CI
        seed: Random seed
        
    Returns:
        Dictionary mapping metric names to BootstrapResult
    """
    results = {}
    
    for metric, values in data.items():
        if 'baseline' not in values or 'post' not in values:
            raise ValueError(f"Metric {metric} must have 'baseline' and 'post' keys")
            
        result = calculate_bootstrap_ci(
            baseline_values=values['baseline'],
            post_values=values['post'],
            n_resamples=n_resamples,
            confidence_level=confidence_level,
            seed=seed
        )
        result.metric = metric
        results[metric] = result
        
    return results

def main():
    """
    Main entry point for bootstrap analysis.
    Reads merged data, calculates bootstrap CIs, and writes results to JSON.
    """
    # Set up paths
    project_root = Path(__file__).resolve().parent.parent.parent
    data_dir = project_root / "data" / "processed"
    results_dir = project_root / "results"
    
    # Ensure results directory exists
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Load merged data
    merged_data_path = data_dir / "merged_baseline_post.csv"
    if not merged_data_path.exists():
        print(f"Error: Merged data file not found at {merged_data_path}")
        return
        
    # Read merged data
    metrics_data = {}
    with open(merged_data_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
    # Group by metric
    for row in rows:
        metric = row['metric']
        if metric not in metrics_data:
            metrics_data[metric] = {'baseline': [], 'post': []}
        
        if row['phase'] == 'baseline':
            metrics_data[metric]['baseline'].append(float(row['value']))
        elif row['phase'] == 'post':
            metrics_data[metric]['post'].append(float(row['value']))
    
    # Run bootstrap analysis
    results = run_bootstrap_analysis(
        data=metrics_data,
        n_resamples=10000,
        confidence_level=0.95,
        seed=42
    )
    
    # Write results to JSON
    output_path = results_dir / "bootstrap_results.json"
    with open(output_path, 'w') as f:
        json_results = {
            metric: {
                'mean_change': result.mean_change,
                'ci_lower': result.ci_lower,
                'ci_upper': result.ci_upper,
                'p_value': result.p_value,
                'n_resamples': result.n_resamples,
                'convergence': result.convergence
            }
            for metric, result in results.items()
        }
        json.dump(json_results, f, indent=2)
        
    print(f"Bootstrap analysis complete. Results written to {output_path}")
    
    # Print summary
    for metric, result in results.items():
        print(f"{metric}: mean_change={result.mean_change:.4f}, "
              f"95% CI=[{result.ci_lower:.4f}, {result.ci_upper:.4f}], "
              f"p={result.p_value:.4f}")

if __name__ == "__main__":
    main()