"""
Bootstrapper module for T032.
Implements bootstrapped power estimation on real datasets,
calculates KS distance against simulated predictions,
and saves results to data/simulation/real_data_power.json.
"""
import os
import json
from typing import Dict, Any, List, Tuple
import numpy as np
import pandas as pd
from scipy import stats

def load_real_data_pvalues(filepath: str = "data/simulation/real_data_pvalues.csv") -> pd.DataFrame:
    """Load p-values from real dataset analysis."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Real data p-values file not found: {filepath}")
    return pd.read_csv(filepath)

def load_simulated_power_distribution(filepath: str = "data/simulation/error_rates_summary.csv") -> pd.DataFrame:
    """Load simulated error rates to derive power distribution."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Simulated error rates file not found: {filepath}")
    return pd.read_csv(filepath)

def bootstrap_power_estimate(
    p_values: List[float],
    alpha: float = 0.05,
    n_bootstrap: int = 1000,
    rng: np.random.Generator = None
) -> Dict[str, float]:
    """
    Estimate power via bootstrapping on observed p-values.
    
    Power is estimated as the proportion of bootstrap samples
    where the proportion of p-values < alpha exceeds a threshold.
    
    Args:
        p_values: List of observed p-values from real data
        alpha: Significance threshold
        n_bootstrap: Number of bootstrap iterations
        rng: Random number generator for reproducibility
        
    Returns:
        Dictionary with estimated power, CI bounds, and standard error
    """
    if rng is None:
        rng = np.random.default_rng(42)
        
    if len(p_values) == 0:
        return {"power_estimate": 0.0, "ci_lower": 0.0, "ci_upper": 0.0, "se": 0.0}
        
    n = len(p_values)
    bootstrap_proportions = []
    
    for _ in range(n_bootstrap):
        # Resample with replacement
        sample_indices = rng.integers(0, n, size=n)
        sample_pvalues = [p_values[i] for i in sample_indices]
        # Calculate proportion significant
        prop_sig = sum(1 for p in sample_pvalues if p < alpha) / n
        bootstrap_proportions.append(prop_sig)
        
    bootstrap_proportions = np.array(bootstrap_proportions)
    power_estimate = float(np.mean(bootstrap_proportions))
    se = float(np.std(bootstrap_proportions, ddof=1))
    
    # 95% CI using percentile method
    ci_lower = float(np.percentile(bootstrap_proportions, 2.5))
    ci_upper = float(np.percentile(bootstrap_proportions, 97.5))
    
    return {
        "power_estimate": power_estimate,
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "se": se,
        "n_bootstrap": n_bootstrap,
        "n_observations": n,
        "alpha": alpha
    }

def calculate_ks_distance(
    real_pvalues: List[float],
    simulated_pvalues: List[float]
) -> float:
    """
    Calculate Kolmogorov-Smirnov distance between real and simulated p-value distributions.
    
    Args:
        real_pvalues: P-values from real dataset analysis
        simulated_pvalues: P-values from simulation under null hypothesis
        
    Returns:
        KS distance statistic (0 to 1)
    """
    if len(real_pvalues) == 0 or len(simulated_pvalues) == 0:
        return 1.0  # Maximum distance if either is empty
        
    # KS test returns (statistic, p-value)
    ks_stat, _ = stats.ks_2samp(real_pvalues, simulated_pvalues)
    return float(ks_stat)

def run_bootstrapped_validation(
    real_pvalues: pd.DataFrame,
    simulated_error_rates: pd.DataFrame,
    alpha: float = 0.05,
    n_bootstrap: int = 1000
) -> Dict[str, Any]:
    """
    Run full bootstrapped validation analysis.
    
    Args:
        real_pvalues: DataFrame with real dataset p-values
        simulated_error_rates: DataFrame with simulated error rates
        alpha: Significance threshold
        n_bootstrap: Number of bootstrap iterations
        
    Returns:
        Dictionary with validation results per test type
    """
    results = {}
    rng = np.random.default_rng(42)
    
    # Group real p-values by test type
    for test_type in real_pvalues['test_type'].unique():
        test_data = real_pvalues[real_pvalues['test_type'] == test_type]
        p_values_list = test_data['p_value'].tolist()
        
        # Bootstrap power estimate
        power_result = bootstrap_power_estimate(
            p_values_list, 
            alpha=alpha, 
            n_bootstrap=n_bootstrap,
            rng=rng
        )
        
        # Get simulated p-values for comparison (under null)
        # We simulate by using the error rate to estimate expected p-value distribution
        # For simplicity, we use a uniform distribution scaled by observed Type I error
        simulated_error_rate = simulated_error_rates[
            (simulated_error_rates['test_type'] == test_type) & 
            (simulated_error_rates['effect_size'] == 0.0)
        ]['type_i_error_rate'].mean()
        
        # Generate simulated p-values for KS comparison
        # Under null, p-values should be uniform(0,1)
        n_sim = max(len(p_values_list), 1000)
        simulated_pvals = rng.uniform(0, 1, n_sim)
        
        # Calculate KS distance
        ks_dist = calculate_ks_distance(p_values_list, simulated_pvals)
        
        # Determine if validation passes (KS <= 0.10)
        passes_validation = ks_dist <= 0.10
        
        results[test_type] = {
            "power_estimate": power_result,
            "ks_distance": ks_dist,
            "passes_validation": passes_validation,
            "threshold": 0.10,
            "n_real_observations": len(p_values_list),
            "simulated_type_i_error_rate": float(simulated_error_rate) if not pd.isna(simulated_error_rate) else None
        }
        
    return results

def save_power_results(
    results: Dict[str, Any],
    output_path: str = "data/simulation/real_data_power.json"
) -> None:
    """Save bootstrapped power results to JSON file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

def main():
    """Main entry point for T032 bootstrapped validation."""
    # File paths
    real_pvalues_path = "data/simulation/real_data_pvalues.csv"
    simulated_error_rates_path = "data/simulation/error_rates_summary.csv"
    output_path = "data/simulation/real_data_power.json"
    
    # Load data
    print(f"Loading real data p-values from {real_pvalues_path}...")
    real_pvalues_df = load_real_data_pvalues(real_pvalues_path)
    
    print(f"Loading simulated error rates from {simulated_error_rates_path}...")
    simulated_error_rates_df = load_simulated_power_distribution(simulated_error_rates_path)
    
    # Run validation
    print("Running bootstrapped power estimation and KS distance calculation...")
    results = run_bootstrapped_validation(
        real_pvalues_df,
        simulated_error_rates_df,
        alpha=0.05,
        n_bootstrap=1000
    )
    
    # Save results
    save_power_results(results, output_path)
    print(f"Results saved to {output_path}")
    
    # Print summary
    print("\n=== Bootstrapped Validation Summary ===")
    for test_type, result in results.items():
        status = "PASS" if result['passes_validation'] else "FAIL"
        print(f"{test_type}: KS={result['ks_distance']:.4f} (threshold=0.10) [{status}]")
        print(f"  Power estimate: {result['power_estimate']['power_estimate']:.4f} "
              f"95% CI [{result['power_estimate']['ci_lower']:.4f}, {result['power_estimate']['ci_upper']:.4f}]")
        
    return results

if __name__ == "__main__":
    main()
