import os
import json
import csv
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from scipy import stats
from code.simulation.output_writer import load_p_values_raw
from code.analysis.bootstrapper import load_real_data_pvalues, calculate_ks_distance

def load_simulated_pvalues_for_comparison() -> pd.DataFrame:
    """Load simulated p-values for comparison with real data."""
    return load_p_values_raw()

def calculate_real_data_power(p_values: List[float], alpha: float = 0.05) -> float:
    """
    Calculate empirical power from real data p-values.
    Power is estimated as the proportion of tests that reject the null hypothesis.
    """
    if not p_values:
        return 0.0
    rejections = sum(1 for p in p_values if p < alpha)
    return rejections / len(p_values)

def calculate_ks_distance(simulated_pvalues: List[float], real_pvalues: List[float]) -> float:
    """
    Calculate Kolmogorov-Smirnov distance between simulated and real p-value distributions.
    """
    if not simulated_pvalues or not real_pvalues:
        return float('inf')
    ks_stat, _ = stats.ks_2samp(simulated_pvalues, real_pvalues)
    return ks_stat

def calculate_validation_metrics(
    simulated_pvalues: List[float],
    real_pvalues: Dict[str, List[float]],
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Calculate comprehensive validation metrics including KS distance and power estimates.
    """
    metrics = {
        "alpha": alpha,
        "simulated_power": calculate_real_data_power(simulated_pvalues, alpha),
        "test_metrics": {}
    }

    for test_type, r_pvals in real_pvalues.items():
        real_power = calculate_real_data_power(r_pvals, alpha)
        ks_dist = calculate_ks_distance(simulated_pvalues, r_pvals)
        
        metrics["test_metrics"][test_type] = {
            "real_power": real_power,
            "ks_distance": ks_dist,
            "sample_size": len(r_pvals),
            "passed_ks_threshold": ks_dist <= 0.10
        }

    # Overall validation status
    all_passed = all(
        m["passed_ks_threshold"] 
        for m in metrics["test_metrics"].values()
    )
    metrics["overall_validation_passed"] = all_passed
    metrics["total_real_samples"] = sum(len(v) for v in real_pvalues.values())

    return metrics

def save_validation_metrics(metrics: Dict[str, Any], output_path: str) -> None:
    """Save validation metrics to a JSON file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)

def main():
    """Main entry point for validation metrics calculation."""
    print("Loading simulated p-values...")
    try:
        df_sim = load_p_values_raw()
        if df_sim is None or df_sim.empty:
            print("Error: No simulated p-values found. Run simulation first.")
            return
        
        # Use all simulated p-values for comparison
        simulated_pvalues = df_sim['p_value'].tolist()
    except Exception as e:
        print(f"Error loading simulated p-values: {e}")
        return

    print("Loading real data p-values...")
    try:
        real_pvalues = load_real_data_pvalues()
        if not real_pvalues:
            print("Error: No real data p-values found. Run validation first.")
            return
    except Exception as e:
        print(f"Error loading real data p-values: {e}")
        return

    print("Calculating validation metrics...")
    metrics = calculate_validation_metrics(simulated_pvalues, real_pvalues)

    output_path = "data/simulation/validation_metrics.json"
    print(f"Saving validation metrics to {output_path}...")
    save_validation_metrics(metrics, output_path)

    print(f"Validation complete. Overall passed: {metrics['overall_validation_passed']}")
    print(f"KS distances: { {k: v['ks_distance'] for k, v in metrics['test_metrics'].items()} }")

if __name__ == "__main__":
    main()