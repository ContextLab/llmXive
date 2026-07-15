import os
import json
from typing import Dict, Any, List, Tuple
import numpy as np
import pandas as pd
from scipy import stats

# Paths
REAL_DATA_PVALUES_PATH = "data/simulation/real_data_pvalues.csv"
SIMULATED_POWER_PATH = "data/simulation/simulated_power_distribution.json"
POWER_RESULTS_PATH = "data/simulation/real_data_power.json"

def load_real_data_pvalues(pvalues_path: str = REAL_DATA_PVALUES_PATH) -> List[float]:
    """Load real data p-values from CSV."""
    if not os.path.exists(pvalues_path):
        raise FileNotFoundError(f"Real data p-values file not found: {pvalues_path}")
    
    df = pd.read_csv(pvalues_path)
    if 'p_value' not in df.columns:
        raise ValueError(f"Column 'p_value' not found in {pvalues_path}")
    
    return df['p_value'].dropna().tolist()

def load_simulated_power_distribution(power_path: str = SIMULATED_POWER_PATH) -> Dict[str, Any]:
    """Load simulated power distribution from JSON."""
    if not os.path.exists(power_path):
        raise FileNotFoundError(f"Simulated power distribution file not found: {power_path}")
    
    with open(power_path, 'r') as f:
        return json.load(f)

def bootstrap_power_estimate(
    pvalues: List[float],
    n_bootstrap: int = 1000,
    alpha: float = 0.05,
    random_seed: int = 42
) -> Dict[str, Any]:
    """
    Perform bootstrapped power estimation on p-values.
    Returns point estimate and confidence interval.
    """
    if not pvalues:
        return {"estimate": None, "ci_lower": None, "ci_upper": None}
    
    np.random.seed(random_seed)
    n = len(pvalues)
    bootstrap_estimates = []
    
    for _ in range(n_bootstrap):
        # Resample with replacement
        sample = np.random.choice(pvalues, size=n, replace=True)
        # Calculate proportion significant (power estimate)
        power = np.mean(np.array(sample) < alpha)
        bootstrap_estimates.append(power)
    
    bootstrap_estimates = np.array(bootstrap_estimates)
    
    return {
        "point_estimate": float(np.mean(bootstrap_estimates)),
        "ci_lower": float(np.percentile(bootstrap_estimates, 2.5)),
        "ci_upper": float(np.percentile(bootstrap_estimates, 97.5)),
        "std_error": float(np.std(bootstrap_estimates)),
        "n_bootstrap": n_bootstrap,
        "original_sample_size": n
    }

def calculate_ks_distance(simulated: List[float], real: List[float]) -> Dict[str, Any]:
    """Calculate Kolmogorov-Smirnov distance between two distributions."""
    if not simulated or not real:
        return {"ks_statistic": None, "p_value": None}
    
    try:
        ks_stat, p_val = stats.ks_2samp(simulated, real)
        return {
            "ks_statistic": float(ks_stat),
            "p_value": float(p_val),
            "valid": True
        }
    except Exception as e:
        return {
            "ks_statistic": None,
            "p_value": None,
            "valid": False,
            "error": str(e)
        }

def run_bootstrapped_validation(
    real_pvalues_path: str = REAL_DATA_PVALUES_PATH,
    simulated_pvalues_path: str = "data/simulation/p_values_raw.csv",
    n_bootstrap: int = 1000,
    alpha: float = 0.05,
    random_seed: int = 42
) -> Dict[str, Any]:
    """
    Run full bootstrapped validation pipeline.
    """
    # Load data
    real_pvalues = load_real_data_pvalues(real_pvalues_path)
    
    # Load simulated p-values for comparison
    if not os.path.exists(simulated_pvalues_path):
        raise FileNotFoundError(f"Simulated p-values file not found: {simulated_pvalues_path}")
    
    df_sim = pd.read_csv(simulated_pvalues_path)
    simulated_pvalues = df_sim['p_value'].dropna().tolist()
    
    # Calculate bootstrapped power estimate
    power_estimate = bootstrap_power_estimate(
        real_pvalues, 
        n_bootstrap=n_bootstrap, 
        alpha=alpha, 
        random_seed=random_seed
    )
    
    # Calculate KS distance
    ks_result = calculate_ks_distance(simulated_pvalues, real_pvalues)
    
    # Compile results
    results = {
        "timestamp": str(np.datetime64('now')),
        "real_data": {
            "sample_size": len(real_pvalues),
            "bootstrap_power": power_estimate
        },
        "comparison": {
            "ks_distance": ks_result
        },
        "validation_passed": ks_result.get("ks_statistic") is not None and ks_result["ks_statistic"] <= 0.10
    }
    
    return results

def save_power_results(results: Dict[str, Any], output_path: str = POWER_RESULTS_PATH) -> str:
    """Save power estimation results to JSON."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    return output_path

def main():
    """Main entry point for bootstrapped validation."""
    print("Running bootstrapped power estimation and validation...")
    
    try:
        results = run_bootstrapped_validation()
        output_path = save_power_results(results)
        
        print(f"Results saved to: {output_path}")
        print(f"Validation passed: {results['validation_passed']}")
        print(f"KS Statistic: {results['comparison']['ks_distance'].get('ks_statistic')}")
        
        return 0
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
