import os
import json
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from scipy import stats
import pandas as pd

def bootstrap_power_estimate(
    p_values: List[float],
    n_iterations: int = 1000,
    alpha: float = 0.05,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Perform bootstrapped power estimation on a list of p-values.
    
    Args:
        p_values: List of observed p-values from real data tests.
        n_iterations: Number of bootstrap iterations.
        alpha: Significance threshold.
        seed: Random seed for reproducibility.
        
    Returns:
        Dictionary with bootstrap statistics including estimated power,
        confidence intervals, and standard error.
    """
    if seed is not None:
        np.random.seed(seed)
        
    if not p_values:
        return {
            "estimated_power": 0.0,
            "ci_lower": 0.0,
            "ci_upper": 0.0,
            "standard_error": 0.0,
            "n_samples": 0,
            "n_iterations": n_iterations
        }
        
    p_array = np.array(p_values)
    n = len(p_array)
    significant_count = np.sum(p_array < alpha)
    
    # Bootstrap sampling to estimate power distribution
    bootstrap_powers = []
    for _ in range(n_iterations):
        # Resample with replacement
        resampled = np.random.choice(p_array, size=n, replace=True)
        # Calculate power as proportion of significant results
        power = np.mean(resampled < alpha)
        bootstrap_powers.append(power)
        
    bootstrap_powers = np.array(bootstrap_powers)
    
    return {
        "estimated_power": float(np.mean(bootstrap_powers)),
        "ci_lower": float(np.percentile(bootstrap_powers, 2.5)),
        "ci_upper": float(np.percentile(bootstrap_powers, 97.5)),
        "standard_error": float(np.std(bootstrap_powers)),
        "n_samples": n,
        "n_iterations": n_iterations,
        "observed_significant_rate": float(significant_count / n) if n > 0 else 0.0
    }

def calculate_ks_distance(
    real_data_p_values: List[float],
    simulated_power_dist: List[float]
) -> float:
    """
    Calculate Kolmogorov-Smirnov distance between real data p-value distribution
    and simulated power distribution.
    
    Args:
        real_data_p_values: Observed p-values from real datasets.
        simulated_power_dist: Simulated power distribution values.
        
    Returns:
        KS distance statistic.
    """
    if not real_data_p_values or not simulated_power_dist:
        return 0.0
        
    # Convert to cumulative distribution functions
    real_dist = np.sort(real_data_p_values)
    sim_dist = np.sort(simulated_power_dist)
    
    # Use scipy's KS test
    ks_stat, _ = stats.ks_2samp(real_dist, sim_dist)
    return float(ks_stat)

def load_simulated_power_distribution(
    path: str = "data/simulation/error_rates_summary.csv"
) -> List[float]:
    """
    Load simulated power distribution from aggregated results.
    
    Args:
        path: Path to the error rates summary CSV.
        
    Returns:
        List of power values (1 - Type II error rate) from simulations.
    """
    if not os.path.exists(path):
        return []
        
    df = pd.read_csv(path)
    # Power is typically 1 - Type II error rate
    # Assuming column 'power' or '1_minus_type_ii' exists
    if 'power' in df.columns:
        return df['power'].tolist()
    elif '1_minus_type_ii' in df.columns:
        return df['1_minus_type_ii'].tolist()
    else:
        # Fallback: calculate from Type II error if available
        if 'type_ii_error' in df.columns:
            return (1 - df['type_ii_error']).tolist()
        else:
            return []

def run_bootstrapped_validation(
    real_p_values: List[float],
    simulated_power_dist: List[float],
    n_bootstrap_iterations: int = 1000,
    alpha: float = 0.05,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Run complete bootstrapped validation pipeline.
    
    Args:
        real_p_values: Observed p-values from real datasets.
        simulated_power_dist: Simulated power distribution for comparison.
        n_bootstrap_iterations: Number of bootstrap iterations.
        alpha: Significance threshold.
        seed: Random seed.
        
    Returns:
        Dictionary containing all validation metrics.
    """
    # Calculate bootstrap power estimate for real data
    bootstrap_result = bootstrap_power_estimate(
        p_values=real_p_values,
        n_iterations=n_bootstrap_iterations,
        alpha=alpha,
        seed=seed
    )
    
    # Calculate KS distance
    ks_distance = calculate_ks_distance(real_p_values, simulated_power_dist)
    
    # Determine if validation passed (KS <= 0.10)
    validation_passed = ks_distance <= 0.10
    
    return {
        "bootstrap_power": bootstrap_result,
        "ks_distance": ks_distance,
        "validation_passed": validation_passed,
        "threshold": 0.10,
        "alpha": alpha,
        "n_bootstrap_iterations": n_bootstrap_iterations
    }

def save_power_results(
    results: Dict[str, Any],
    output_path: str = "data/simulation/real_data_power.json"
) -> None:
    """
    Save bootstrapped power estimation results to JSON file.
    
    Args:
        results: Dictionary of results to save.
        output_path: Path to output JSON file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

def main() -> None:
    """Main entry point for bootstrapped power validation."""
    # Load real data p-values (generated by T031)
    real_pvalues_path = "data/simulation/real_data_pvalues.csv"
    if not os.path.exists(real_pvalues_path):
        print(f"Error: Real data p-values file not found at {real_pvalues_path}")
        print("Please run T031 first to generate real_data_pvalues.csv")
        return
        
    df_real = pd.read_csv(real_pvalues_path)
    
    # Collect all p-values from the dataset
    all_p_values = df_real['p_value'].tolist()
    
    # Load simulated power distribution for comparison
    simulated_dist = load_simulated_power_distribution()
    
    if not simulated_dist:
        print("Warning: Could not load simulated power distribution. Using empty comparison.")
        simulated_dist = [0.5] * len(all_p_values)  # Fallback for KS calculation
        
    # Run bootstrapped validation
    results = run_bootstrapped_validation(
        real_p_values=all_p_values,
        simulated_power_dist=simulated_dist,
        n_bootstrap_iterations=1000,
        alpha=0.05,
        seed=42
    )
    
    # Save results
    output_path = "data/simulation/real_data_power.json"
    save_power_results(results, output_path)
    print(f"Bootstrapped power validation results saved to {output_path}")
    print(f"KS Distance: {results['ks_distance']:.4f}")
    print(f"Validation Passed (KS <= 0.10): {results['validation_passed']}")
    print(f"Estimated Power: {results['bootstrap_power']['estimated_power']:.4f}")
    print(f"Power 95% CI: [{results['bootstrap_power']['ci_lower']:.4f}, {results['bootstrap_power']['ci_upper']:.4f}]")

if __name__ == "__main__":
    main()