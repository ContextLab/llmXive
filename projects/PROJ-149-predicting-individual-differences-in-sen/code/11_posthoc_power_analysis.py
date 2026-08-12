"""
T023: Perform post-hoc power analysis to estimate required sample size.

Estimation target: R² = 0.10 with Power ≥ 0.80.
Input: data/processed/model_results.json (from T019).
Output: Appends 'power_analysis' section to data/processed/model_results.json.
"""
import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path for imports if running as script
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config import get_path, get_seed
from utils.stats_helpers import calculate_sample_size_for_r2

def load_model_results() -> Dict[str, Any]:
    """Load the model results JSON file."""
    path = get_path("model_results", "processed")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Model results file not found at {path}. "
                                "Ensure T019 (modeling) has completed successfully.")
    with open(path, 'r') as f:
        return json.load(f)

def perform_power_analysis(results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Perform post-hoc power analysis to estimate required N for R²=0.10, power=0.80.
    
    Uses the actual sample size (N) from the current study and the observed R²
    to estimate the required sample size for the target effect size.
    """
    # Extract observed metrics
    observed_n = results.get('final_n', None)
    observed_r2 = results.get('adjusted_r2', None)
    
    if observed_n is None or observed_r2 is None:
        raise ValueError("Cannot perform power analysis: missing 'final_n' or 'adjusted_r2' in model_results.json.")

    # Target parameters as per FR-011
    target_r2 = 0.10
    target_power = 0.80
    alpha = 0.05
    
    # Estimate number of predictors (k) from the features used.
    # We assume the features are the band powers (delta, theta, alpha, low-beta, high-beta, gamma) + potentially others.
    # A safe estimate for k in this context is 6 (the bands) or we can count columns if available.
    # For robustness, we default to k=6 if not explicitly stored, as per the band definition.
    k = results.get('num_predictors', 6) 
    
    # Calculate required sample size
    required_n = calculate_sample_size_for_r2(
        effect_size_f2=target_r2 / (1 - target_r2), # f2 = R2 / (1-R2)
        alpha=alpha,
        power=target_power,
        k=k
    )
    
    # Calculate achieved power with current N and observed R² (for context)
    # Note: statsmodels FTestPower.f_power requires f2, n, k, alpha
    # f2 = R2 / (1-R2)
    observed_f2 = observed_r2 / (1 - observed_r2) if observed_r2 < 1.0 else 0.99
    
    from statsmodels.stats.power import FTestPower
    ftest = FTestPower()
    achieved_power = ftest.power(
        effect_size=observed_f2,
        nobs=observed_n,
        df_num=k,
        df_denom=observed_n - k - 1,
        alpha=alpha
    )
    
    power_analysis = {
        "target_r2": target_r2,
        "target_power": target_power,
        "alpha": alpha,
        "num_predictors_k": k,
        "observed_n": observed_n,
        "observed_r2": observed_r2,
        "achieved_power": achieved_power,
        "required_n_for_target": required_n,
        "power_deficit": max(0, required_n - observed_n)
    }
    
    return power_analysis

def save_results(power_analysis: Dict[str, Any]) -> None:
    """Append power analysis results to the model_results.json file."""
    path = get_path("model_results", "processed")
    
    # Load existing results
    results = load_model_results()
    
    # Append or update the power analysis section
    results['power_analysis'] = power_analysis
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    with open(path, 'w') as f:
        json.dump(results, f, indent=2)
        
    print(f"Power analysis results appended to {path}")

def main():
    parser = argparse.ArgumentParser(description="Perform post-hoc power analysis (T023).")
    parser.parse_args()
    
    try:
        results = load_model_results()
        power_analysis = perform_power_analysis(results)
        save_results(power_analysis)
        print("Task T023 completed successfully.")
    except Exception as e:
        print(f"Error during T023 execution: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
