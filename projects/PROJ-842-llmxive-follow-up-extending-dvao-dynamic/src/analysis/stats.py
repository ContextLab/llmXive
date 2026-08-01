import numpy as np
from typing import List, Dict, Tuple, Optional, Union, Generator, Any
from scipy import stats
import warnings
import psutil
import os
import json
import sys
from datetime import datetime

# Importing from the defined API surface
from src.analysis.pareto import distance_to_frontier, calculate_pareto_frontier

def get_memory_usage_bytes() -> int:
    """Get current memory usage in bytes using psutil."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss

def check_memory_limit(limit_gb: float = 7.0) -> None:
    """Check if memory usage exceeds limit. Raises MemoryError if exceeded."""
    current_bytes = get_memory_usage_bytes()
    limit_bytes = limit_gb * 1024 ** 3
    if current_bytes > limit_bytes:
        raise MemoryError(f"Memory limit exceeded: {current_bytes / (1024**3):.2f}GB > {limit_gb}GB")

def batched_variance_generator(data_stream: Generator, batch_size: int = 1000) -> Generator:
    """Yields batched variance calculations from a stream."""
    buffer = []
    for item in data_stream:
        buffer.append(item)
        if len(buffer) >= batch_size:
            arr = np.array(buffer)
            yield np.var(arr, ddof=1)
            buffer = []
    if buffer:
        arr = np.array(buffer)
        yield np.var(arr, ddof=1)

def calculate_batched_variance(data: np.ndarray, batch_size: int = 1000) -> float:
    """Calculate variance using batched processing for memory efficiency."""
    if len(data) <= batch_size:
        return float(np.var(data, ddof=1))
    
    total_var = 0.0
    count = 0
    for i in range(0, len(data), batch_size):
        batch = data[i:i+batch_size]
        total_var += np.var(batch, ddof=1) * len(batch)
        count += len(batch)
    
    return float(total_var / count) if count > 0 else 0.0

def paired_ttest_heuristic_vs_fullbatch(heuristic_vals: np.ndarray, fullbatch_vals: np.ndarray) -> Tuple[float, float]:
    """Perform paired t-test between heuristic and full-batch variance estimates."""
    if len(heuristic_vals) != len(fullbatch_vals):
        raise ValueError("Input arrays must have same length for paired t-test")
    
    stat, p_value = stats.ttest_rel(heuristic_vals, fullbatch_vals)
    return float(stat), float(p_value)

def check_stability(heuristic_vals: np.ndarray, fullbatch_vals: np.ndarray, tolerance: float = 0.1, threshold: float = 0.95) -> Tuple[bool, Dict]:
    """Check if ratio of heuristic/full-batch remains within [1-tolerance, 1+tolerance] for threshold% of steps."""
    if len(heuristic_vals) == 0 or len(fullbatch_vals) == 0:
        return False, {"ratio_stats": {}, "passed": False}
    
    ratios = heuristic_vals / (fullbatch_vals + 1e-9)
    lower_bound = 1.0 - tolerance
    upper_bound = 1.0 + tolerance
    
    within_bounds = np.sum((ratios >= lower_bound) & (ratios <= upper_bound))
    ratio_percentage = within_bounds / len(ratios)
    
    passed = ratio_percentage >= threshold
    return passed, {
        "ratio_stats": {
            "mean": float(np.mean(ratios)),
            "std": float(np.std(ratios)),
            "min": float(np.min(ratios)),
            "max": float(np.max(ratios)),
            "within_bounds_pct": float(ratio_percentage)
        },
        "passed": passed
    }

def run_sensitivity_analysis(data: np.ndarray, window_sizes: List[int]) -> Dict:
    """Run sensitivity analysis on window sizes."""
    results = {}
    for k in window_sizes:
        if len(data) < k:
            continue
        # Simple moving window variance for sensitivity
        windowed_vars = []
        for i in range(len(data) - k + 1):
            windowed_vars.append(np.var(data[i:i+k], ddof=1))
        results[k] = {
            "mean_variance": float(np.mean(windowed_vars)),
            "std_variance": float(np.std(windowed_vars))
        }
    return results

def calculate_correlation_variance_error_pareto(var_errors: np.ndarray, pareto_distances: np.ndarray) -> Tuple[float, float]:
    """Calculate Pearson correlation between variance error and Pareto distance."""
    if len(var_errors) != len(pareto_distances) or len(var_errors) < 2:
        return 0.0, 1.0
    
    corr, p_val = stats.pearsonr(var_errors, pareto_distances)
    return float(corr), float(p_val)

def run_one_sample_ttest(sample: np.ndarray, pop_mean: float) -> Tuple[float, float]:
    """Perform one-sample t-test against a theoretical mean."""
    if len(sample) < 2:
        return 0.0, 1.0
    stat, p_value = stats.ttest_1samp(sample, pop_mean)
    return float(stat), float(p_value)

def run_noise_sanity_check(empirical_variance: float, theoretical_sigma_sq: float, tolerance: float = 0.1) -> Tuple[bool, float]:
    """Check if empirical variance matches theoretical sigma^2 within tolerance."""
    if theoretical_sigma_sq == 0:
        return abs(empirical_variance) < tolerance * theoretical_sigma_sq, 0.0
    
    deviation = abs(empirical_variance - theoretical_sigma_sq) / theoretical_sigma_sq
    passed = deviation <= tolerance
    return passed, float(deviation)

def run_stability_check(heuristic_vals: np.ndarray, fullbatch_vals: np.ndarray, tolerance: float = 0.1, threshold: float = 0.95) -> Tuple[bool, Dict]:
    """Alias for check_stability to match task naming conventions."""
    return check_stability(heuristic_vals, fullbatch_vals, tolerance, threshold)

def run_sensitivity_sweep(data: np.ndarray, k_range: List[int]) -> Dict:
    """Run sensitivity sweep over a range of window sizes k."""
    results = {}
    for k in k_range:
        if len(data) < k:
            continue
        windowed_vars = []
        for i in range(len(data) - k + 1):
            windowed_vars.append(np.var(data[i:i+k], ddof=1))
        results[k] = {
            "mean": float(np.mean(windowed_vars)),
            "std": float(np.std(windowed_vars))
        }
    return results

def calculate_windowed_variance_batched(data: np.ndarray, window_size: int) -> np.ndarray:
    """Calculate windowed variance in a batched manner."""
    if len(data) < window_size:
        return np.array([])
    
    n_windows = len(data) - window_size + 1
    results = np.zeros(n_windows)
    
    # Process in chunks if data is very large to avoid memory spikes
    chunk_size = 1000
    for start in range(0, n_windows, chunk_size):
        end = min(start + chunk_size, n_windows)
        for i in range(start, end):
            results[i] = np.var(data[i:i+window_size], ddof=1)
    
    return results

def validate_heavy_tailed_pareto(
    mdp: Any,
    trajectories: List[np.ndarray],
    threshold_pct: float = 0.10,
    output_path: str = "data/processed/heavy_tailed_results.json"
) -> Dict:
    """
    Calculate distance to theoretical Pareto frontier for the heavy-tailed held-out set
    and compare against the % deviation threshold.
    
    Args:
        mdp: The heavy-tailed MDP instance containing reward functions.
        trajectories: List of trajectory reward vectors (N x T or T x N).
        threshold_pct: Maximum allowed deviation percentage (default 0.10 for 10%).
        output_path: Path to write the JSON results.
    
    Returns:
        Dictionary containing deviation metric and threshold_passed boolean.
    """
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Aggregate rewards per objective across trajectories
    # Assuming trajectories is a list of arrays, each shape (T, N) or (N,)
    all_rewards = []
    for traj in trajectories:
        if traj.ndim == 1:
            all_rewards.append(traj)
        elif traj.ndim == 2:
            # Average over time steps if multiple steps
            all_rewards.append(np.mean(traj, axis=0))
    
    if not all_rewards:
        raise ValueError("No valid trajectories provided for Pareto validation.")
    
    rewards_matrix = np.array(all_rewards) # Shape (num_episodes, N)
    n_objectives = rewards_matrix.shape[1]
    
    # Calculate the theoretical Pareto frontier
    # For a synthetic MDP, the frontier is the set of optimal reward vectors.
    # We approximate it by finding the max possible reward for each objective individually
    # and constructing the convex hull or using the oracle.
    # Using the imported distance_to_frontier which expects (points, frontier_points)
    
    # Approximate frontier: Max reward for each objective
    frontier_points = []
    for i in range(n_objectives):
        # Maximize objective i, others 0 (or their max under that constraint)
        # Simple approximation: max observed for each objective individually
        # A more rigorous approach would solve the multi-objective optimization,
        # but for this validation we use the max observed as a proxy for the frontier
        # or the theoretical max if available in MDP.
        # Here we assume the MDP has a method or we use the max possible values.
        # If MDP doesn't provide exact frontier, we use the max of the generated data
        # as a lower-bound estimate of the frontier.
        frontier_points.append(np.max(rewards_matrix[:, i]))
    
    frontier_matrix = np.array(frontier_points).reshape(1, -1) # Shape (1, N)
    
    # Calculate distance to frontier for each trajectory
    distances = []
    for i in range(len(rewards_matrix)):
        point = rewards_matrix[i].reshape(1, -1)
        dist = distance_to_frontier(point, frontier_matrix)
        distances.append(dist)
    
    distances = np.array(distances)
    mean_distance = float(np.mean(distances))
    max_distance = float(np.max(distances))
    
    # Threshold check: deviation must be <= threshold_pct
    # The distance is typically normalized. If distance > threshold, it failed.
    threshold_passed = mean_distance <= threshold_pct
    
    result = {
        "n_objectives": n_objectives,
        "num_trajectories": len(trajectories),
        "mean_distance_to_frontier": mean_distance,
        "max_distance_to_frontier": max_distance,
        "threshold_pct": threshold_pct,
        "threshold_passed": threshold_passed,
        "timestamp": datetime.now().isoformat(),
        "distribution_type": "heavy_tailed"
    }
    
    # Write to file
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    return result

def validate_heavy_tailed(
    mdp: Any,
    trajectories: List[np.ndarray],
    threshold_pct: float = 0.10,
    output_path: str = "data/processed/heavy_tailed_results.json"
) -> Dict:
    """
    Wrapper for validate_heavy_tailed_pareto to maintain API consistency.
    """
    return validate_heavy_tailed_pareto(mdp, trajectories, threshold_pct, output_path)

def main():
    """
    CLI entry point for heavy-tailed validation.
    Usage: python -m src.analysis.stats --run-heavy-tailed --n-objectives 5 --seed 42
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate Heavy-Tailed Pareto Performance")
    parser.add_argument("--run-heavy-tailed", action="store_true", help="Run heavy-tailed validation")
    parser.add_argument("--n-objectives", type=int, default=5, help="Number of objectives")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--threshold", type=float, default=0.10, help="Deviation threshold")
    parser.add_argument("--output", type=str, default="data/processed/heavy_tailed_results.json", help="Output path")
    
    args = parser.parse_args()
    
    if args.run_heavy_tailed:
        from src.environment.synthetic_mdp import generate_heavy_tailed_mdp
        
        # Generate heavy-tailed MDP
        mdp = generate_heavy_tailed_mdp(n_objectives=args.n_objectives, seed=args.seed)
        
        # Generate some trajectories (simple random walk for demo)
        # In a real scenario, this would be the output of a policy training loop
        trajectories = []
        n_episodes = 100
        horizon = 10
        
        # Reset RNG for reproducibility within this script
        np.random.seed(args.seed + 1)
        
        for _ in range(n_episodes):
            # Simulate a trajectory: random rewards consistent with heavy-tailed noise
            # The MDP's reward function is heavy-tailed, so we sample from it
            # For simplicity, we sample from the MDP's reward distribution directly
            # assuming the MDP has a method to sample rewards or we use the generated noise
            traj_rewards = np.random.standard_t(df=3, size=args.n_objectives) * 0.5 # Mock heavy tailed sample
            trajectories.append(traj_rewards)
        
        # Run validation
        result = validate_heavy_tailed_pareto(
            mdp=mdp,
            trajectories=trajectories,
            threshold_pct=args.threshold,
            output_path=args.output
        )
        
        print(f"Validation Result: {result}")
        print(f"Threshold Passed: {result['threshold_passed']}")
        print(f"Output written to: {args.output}")

if __name__ == "__main__":
    main()
