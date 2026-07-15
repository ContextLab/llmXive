import os
import json
import csv
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from scipy import stats

from code.analysis.bootstrapper import load_real_data_pvalues, load_simulated_power_distribution
from code.analysis.real_data_runner import load_p_values_to_csv_safe
from code.utils.metadata_manager import load_simulation_metadata, save_simulation_metadata

# Paths
REAL_DATA_PVALUES_PATH = "data/simulation/real_data_pvalues.csv"
SIMULATED_POWER_PATH = "data/simulation/simulated_power_distribution.json"
VALIDATION_METRICS_PATH = "data/simulation/validation_metrics.json"
METADATA_PATH = "data/simulation_metadata.json"

def load_simulated_pvalues_for_comparison(simulated_pvalues_path: str) -> List[float]:
    """Load simulated p-values for comparison with real data."""
    if not os.path.exists(simulated_pvalues_path):
        raise FileNotFoundError(f"Simulated p-values file not found: {simulated_pvalues_path}")
    
    p_values = []
    with open(simulated_pvalues_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                p_val = float(row['p_value'])
                p_values.append(p_val)
            except (ValueError, KeyError):
                continue
    return p_values

def calculate_real_data_power(real_pvalues: List[float], alpha: float = 0.05) -> Dict[str, Any]:
    """
    Calculate empirical power from real data p-values.
    Since we don't have ground truth in real data, we estimate power based on
    the proportion of significant results, acknowledging this is a limitation.
    """
    if not real_pvalues:
        return {"power_estimate": None, "significant_count": 0, "total_count": 0}
    
    significant_count = sum(1 for p in real_pvalues if p < alpha)
    total_count = len(real_pvalues)
    power_estimate = significant_count / total_count if total_count > 0 else 0.0
    
    return {
        "power_estimate": power_estimate,
        "significant_count": significant_count,
        "total_count": total_count,
        "alpha_threshold": alpha
    }

def calculate_ks_distance(simulated_pvalues: List[float], real_pvalues: List[float]) -> Dict[str, Any]:
    """
    Calculate Kolmogorov-Smirnov distance between simulated and real p-value distributions.
    Returns the KS statistic and p-value for the test.
    """
    if not simulated_pvalues or not real_pvalues:
        return {"ks_statistic": None, "p_value": None, "valid": False}
    
    try:
        ks_stat, p_val = stats.ks_2samp(simulated_pvalues, real_pvalues)
        return {
            "ks_statistic": float(ks_stat),
            "p_value": float(p_val),
            "valid": True,
            "interpretation": "distributions_similar" if p_val > 0.05 else "distributions_different"
        }
    except Exception as e:
        return {
            "ks_statistic": None,
            "p_value": None,
            "valid": False,
            "error": str(e)
        }

def calculate_validation_metrics(
    real_pvalues_path: str = REAL_DATA_PVALUES_PATH,
    simulated_pvalues_path: str = "data/simulation/p_values_raw.csv",
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Calculate comprehensive validation metrics comparing real data to simulation.
    """
    # Load real data p-values
    real_pvalues = load_real_data_pvalues(real_pvalues_path)
    if not real_pvalues:
        raise ValueError(f"No real p-values found in {real_pvalues_path}")
    
    # Load simulated p-values for comparison (filter by test type if needed)
    # For simplicity, we use all simulated p-values, but in a real scenario
    # we would match test types and conditions
    simulated_pvalues = load_simulated_pvalues_for_comparison(simulated_pvalues_path)
    if not simulated_pvalues:
        raise ValueError(f"No simulated p-values found in {simulated_pvalues_path}")
    
    # Calculate power estimates
    real_power = calculate_real_data_power(real_pvalues, alpha)
    
    # Calculate KS distance
    ks_result = calculate_ks_distance(simulated_pvalues, real_pvalues)
    
    # Aggregate metrics
    metrics = {
        "validation_timestamp": str(np.datetime64('now')),
        "real_data": {
            "sample_size": len(real_pvalues),
            "power_estimate": real_power["power_estimate"],
            "significant_proportion": real_power["power_estimate"]
        },
        "simulated_data": {
            "sample_size": len(simulated_pvalues)
        },
        "comparison": {
            "ks_statistic": ks_result.get("ks_statistic"),
            "ks_p_value": ks_result.get("p_value"),
            "distributions_match": ks_result.get("interpretation") == "distributions_similar" if ks_result.get("valid") else None,
            "ks_within_threshold": ks_result.get("ks_statistic") is not None and ks_result["ks_statistic"] <= 0.10
        },
        "validation_status": "passed" if (ks_result.get("ks_statistic") is not None and ks_result["ks_statistic"] <= 0.10) else "failed",
        "notes": "Validation compares real data p-value distribution against simulated null distribution."
    }
    
    return metrics

def save_validation_metrics(metrics: Dict[str, Any], output_path: str = VALIDATION_METRICS_PATH) -> str:
    """Save validation metrics to JSON file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2, default=str)
    
    return output_path

def main():
    """Main entry point for validation metrics calculation."""
    print("Calculating validation metrics...")
    
    try:
        # Calculate metrics
        metrics = calculate_validation_metrics(
            real_pvalues_path=REAL_DATA_PVALUES_PATH,
            simulated_pvalues_path="data/simulation/p_values_raw.csv",
            alpha=0.05
        )
        
        # Save to file
        output_path = save_validation_metrics(metrics)
        print(f"Validation metrics saved to: {output_path}")
        print(f"Validation status: {metrics['validation_status']}")
        print(f"KS Statistic: {metrics['comparison']['ks_statistic']}")
        print(f"KS within threshold (<=0.10): {metrics['comparison']['ks_within_threshold']}")
        
        return 0
    except Exception as e:
        print(f"Error calculating validation metrics: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
