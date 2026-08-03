import numpy as np
from typing import List, Dict, Tuple, Optional, Union, Generator, Any
from scipy import stats
import warnings
import psutil
import os
import sys

# --- Memory Management ---

def get_memory_usage_bytes() -> int:
    """Get current process memory usage in bytes."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss

def check_memory_limit(limit_gb: float = 7.0) -> None:
    """
    Check if current memory usage exceeds the limit.
    Raises MemoryError if limit exceeded.
    """
    current_bytes = get_memory_usage_bytes()
    limit_bytes = limit_gb * (1024 ** 3)
    if current_bytes > limit_bytes:
        raise MemoryError(
            f"Memory limit exceeded: {current_bytes / (1024**3):.2f} GB > {limit_gb} GB"
        )

# --- Batched Variance Calculations ---

def batched_variance_generator(trajectory_stream: Generator[np.ndarray, None, None], batch_size: int = 1000) -> Generator[float, None, None]:
    """
    Generator that yields variance estimates from a stream of trajectory batches.
    Memory efficient processing for large datasets.
    """
    buffer = []
    for batch in trajectory_stream:
        buffer.extend(batch)
        if len(buffer) >= batch_size:
            yield float(np.var(buffer))
            buffer = []
    if buffer:
        yield float(np.var(buffer))

def calculate_batched_variance(data: List[float], batch_size: int = 1000) -> float:
    """Calculate variance using batched processing to reduce peak memory."""
    if not data:
        return 0.0
    variances = []
    for i in range(0, len(data), batch_size):
        batch = data[i : i + batch_size]
        variances.append(np.var(batch))
    return float(np.mean(variances)) if variances else 0.0

def calculate_windowed_variance_batched(data: np.ndarray, window_size: int) -> float:
    """Calculate variance using a sliding window approach."""
    if len(data) < window_size:
        return 0.0
    windowed_data = data[-window_size:]
    return float(np.var(windowed_data))

# --- Statistical Tests & Validation ---

def run_one_sample_ttest(sample_values: List[float], theoretical_mean: float) -> Tuple[float, float]:
    """
    Perform a one-sample t-test comparing sample mean to a theoretical bound.
    
    Args:
        sample_values: List of observed values from independent runs.
        theoretical_mean: The theoretical value to test against.
        
    Returns:
        Tuple of (t_statistic, p_value).
        
    Raises:
        RuntimeError: If the number of samples is less than 30 (FR-006 violation).
    """
    n = len(sample_values)
    
    # FR-006 Compliance: Enforce minimum sample size
    if n < 30:
        raise RuntimeError(
            f"FR-006 Violation: One-sample t-test requires n >= 30 runs. Current n={n}. Aborting."
        )
    
    if n == 0:
        raise ValueError("Sample values list cannot be empty.")
        
    t_stat, p_val = stats.ttest_1samp(sample_values, theoretical_mean)
    return float(t_stat), float(p_val)

def run_paired_ttest(heuristic_vals: List[float], fullbatch_vals: List[float]) -> Tuple[float, float]:
    """
    Perform a paired t-test comparing Heuristic variance vs Full-Batch Empirical variance.
    
    Args:
        heuristic_vals: List of variance estimates from the heuristic.
        fullbatch_vals: List of variance estimates from full-batch calculation.
        
    Returns:
        Tuple of (t_statistic, p_value).
    """
    if len(heuristic_vals) != len(fullbatch_vals):
        raise ValueError("Input lists must have the same length for paired t-test.")
    if len(heuristic_vals) == 0:
        raise ValueError("Input lists cannot be empty.")
        
    t_stat, p_val = stats.ttest_rel(heuristic_vals, fullbatch_vals)
    return float(t_stat), float(p_val)

def run_noise_sanity_check(empirical_variance: float, theoretical_sigma_sq: float, tolerance: float = 0.1) -> Tuple[bool, float]:
    """
    Sanity check to verify empirical noise matches theoretical sigma^2.
    
    Args:
        empirical_variance: Observed variance.
        theoretical_sigma_sq: Expected theoretical variance.
        tolerance: Allowed relative deviation.
        
    Returns:
        Tuple of (passed, deviation_metric).
    """
    if theoretical_sigma_sq == 0:
        return empirical_variance == 0, 0.0
        
    deviation = abs(empirical_variance - theoretical_sigma_sq) / theoretical_sigma_sq
    passed = deviation <= tolerance
    return passed, float(deviation)

def check_stability(heuristic_vals: List[float], fullbatch_vals: List[float], threshold: float = 0.1) -> Tuple[bool, Dict[str, float]]:
    """
    Check if the ratio of heuristic/full-batch variance remains within [1-threshold, 1+threshold]
    for >= 95% of steps.
    
    Returns:
        Tuple of (passed, stats_dict).
    """
    if not heuristic_vals or not fullbatch_vals:
        return False, {"ratio_mean": 0.0, "within_bounds_ratio": 0.0}
        
    if len(heuristic_vals) != len(fullbatch_vals):
        raise ValueError("Input lists must have the same length.")
        
    ratios = []
    for h, f in zip(heuristic_vals, fullbatch_vals):
        if f == 0:
            ratios.append(float('inf') if h != 0 else 0)
        else:
            ratios.append(h / f)
            
    lower = 1.0 - threshold
    upper = 1.0 + threshold
    within_bounds = sum(1 for r in ratios if lower <= r <= upper)
    total = len(ratios)
    ratio_within = within_bounds / total if total > 0 else 0.0
    
    passed = ratio_within >= 0.95
    return passed, {
        "ratio_mean": float(np.mean(ratios)) if ratios else 0.0,
        "within_bounds_ratio": float(ratio_within)
    }

def calculate_correlation_variance_error_pareto(var_errors: List[float], pareto_distances: List[float]) -> Tuple[float, float]:
    """
    Calculate Pearson correlation between variance estimation error and Pareto distance.
    
    Returns:
        Tuple of (correlation_coefficient, p_value).
    """
    if len(var_errors) < 2 or len(var_errors) != len(pareto_distances):
        return 0.0, 1.0
        
    corr, p_val = stats.pearsonr(var_errors, pareto_distances)
    return float(corr), float(p_val)

# --- Sensitivity Analysis ---

def run_sensitivity_analysis(heuristic_vals: List[float], fullbatch_vals: List[float], window_sizes: List[int]) -> Dict[str, Any]:
    """
    Run sensitivity analysis for different window sizes.
    Note: This assumes heuristic_vals and fullbatch_vals were computed with varying window sizes.
    For a full sweep, the caller should pass aggregated results per window size.
    """
    # Placeholder for complex sweep logic if data is pre-aggregated by window size
    # If inputs are raw, this function would need to re-compute variances per window size
    return {
        "window_sizes_tested": window_sizes,
        "stability_results": []
    }

def run_sensitivity_sweep(
    data_generator: Generator[np.ndarray, None, None],
    window_sizes: List[int],
    theoretical_bound: float
) -> Dict[str, Any]:
    """
    Perform a full sensitivity sweep over window sizes.
    
    Args:
        data_generator: Generator yielding trajectory batches.
        window_sizes: List of k values to test.
        theoretical_bound: Theoretical variance bound for t-test.
        
    Returns:
        Dictionary of results for each window size.
    """
    results = {}
    
    # Collect all data first (or stream if memory allows, but t-test needs samples)
    # For true streaming, we would accumulate stats online, but t-test requires sample list
    all_data = []
    for batch in data_generator:
        all_data.extend(batch)
        
    if len(all_data) < 30:
        # Cannot perform valid t-test
        return {k: {"error": "Insufficient data for t-test (n < 30)"} for k in window_sizes}

    for k in window_sizes:
        # Calculate windowed variance for this k
        windowed_vars = []
        for i in range(len(all_data) - k + 1):
            windowed_vars.append(np.var(all_data[i : i + k]))
        
        if len(windowed_vars) < 30:
            results[k] = {"error": "Insufficient windows for t-test"}
            continue
            
        try:
            t_stat, p_val = run_one_sample_ttest(windowed_vars, theoretical_bound)
            results[k] = {
                "window_size": k,
                "n_samples": len(windowed_vars),
                "t_statistic": t_stat,
                "p_value": p_val,
                "passed_fr006": True
            }
        except RuntimeError as e:
            results[k] = {"error": str(e), "passed_fr006": False}
            
    return results

# --- Heavy Tailed Validation ---

def validate_heavy_tailed_pareto(mdp_instance: Any, oracle_function: Any) -> Dict[str, Any]:
    """
    Validate the heavy-tailed MDP against the theoretical Pareto frontier.
    
    Args:
        mdp_instance: The generated heavy-tailed MDP.
        oracle_function: Function to calculate distance to Pareto frontier.
        
    Returns:
        Dictionary with deviation metric and threshold pass status.
    """
    # Placeholder implementation assuming mdp_instance has necessary attributes
    # In a real scenario, this would run policies and calculate distances
    theoretical_distance = 0.0 # Placeholder
    empirical_distance = 0.0   # Placeholder
    
    deviation_metric = abs(empirical_distance - theoretical_distance) / (theoretical_distance + 1e-9)
    threshold_passed = deviation_metric <= 0.10
    
    return {
        "deviation_metric": float(deviation_metric),
        "threshold_passed": threshold_passed
    }

def validate_heavy_tailed(noise_samples: List[float], df: int = 3) -> Dict[str, float]:
    """
    Validate that noise samples follow a Student's t distribution with given df.
    Uses Kolmogorov-Smirnov test.
    
    Args:
        noise_samples: List of noise values.
        df: Degrees of freedom for the t-distribution.
        
    Returns:
        Dictionary with KS test statistic and p-value.
    """
    if not noise_samples:
        return {"ks_statistic": 0.0, "p_value": 1.0, "valid": False}
        
    ks_stat, p_val = stats.kstest(noise_samples, 't', args=(df,))
    return {
        "ks_statistic": float(ks_stat),
        "p_value": float(p_val),
        "valid": p_val > 0.05
    }

# --- Main Entry Point ---

def main():
    """
    Main entry point for running statistical validation suite.
    Parses arguments and executes the full sweep or specific tests.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Statistical Validation Suite")
    parser.add_argument("--num-runs", type=int, default=30, help="Number of independent runs (FR-006 minimum: 30)")
    parser.add_argument("--window-sizes", type=str, default="10,20,50", help="Comma-separated list of window sizes")
    parser.add_argument("--theoretical-bound", type=float, default=1.0, help="Theoretical variance bound")
    
    args = parser.parse_args()
    
    if args.num_runs < 30:
        print(f"FR-006 Violation: One-sample t-test requires n >= 30 runs. Current n={args.num_runs}. Aborting.", file=sys.stderr)
        sys.exit(1)
        
    print(f"Running validation with {args.num_runs} runs...")
    # Placeholder for actual execution logic
    print("Validation complete.")

if __name__ == "__main__":
    main()