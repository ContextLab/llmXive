"""
Validation Metrics Module (Task T034).

Aggregates results from real_data_power.json and calculates summary statistics
to produce data/simulation/validation_metrics.json.

Implements:
- load_simulated_pvalues_for_comparison
- calculate_real_data_power
- calculate_validation_metrics
- save_validation_metrics
- main
"""
import os
import json
import csv
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from scipy import stats

# Local imports matching existing API surface
from code.analysis.bootstrapper import calculate_ks_distance, load_real_data_pvalues
from code.analysis.validator import load_simulation_metadata

# Paths
DATA_DIR = "data/simulation"
REAL_DATA_POWER_PATH = os.path.join(DATA_DIR, "real_data_power.json")
VALIDATION_METRICS_PATH = os.path.join(DATA_DIR, "validation_metrics.json")
REAL_DATA_PVALUES_PATH = os.path.join(DATA_DIR, "real_data_pvalues.csv")
P_VALUES_RAW_PATH = os.path.join(DATA_DIR, "p_values_raw.csv")

def load_simulated_pvalues_for_comparison(sample_size: int, test_type: str) -> List[float]:
    """
    Load simulated p-values from p_values_raw.csv for a specific sample size and test type.
    
    Args:
        sample_size: The sample size to filter by.
        test_type: The test type (e.g., 't-test', 'anova', 'chi-squared').
        
    Returns:
        List of p-values for the specified condition.
    """
    if not os.path.exists(P_VALUES_RAW_PATH):
        raise FileNotFoundError(f"Simulation results not found at {P_VALUES_RAW_PATH}")
        
    p_values = []
    try:
        df = pd.read_csv(P_VALUES_RAW_PATH)
        # Filter by sample_size and test_type
        subset = df[(df['sample_size'] == sample_size) & (df['test_type'] == test_type)]
        if not subset.empty:
            p_values = subset['p_value'].tolist()
    except Exception as e:
        # If file is corrupted or empty, return empty list
        pass
        
    return p_values

def calculate_real_data_power(real_p_values: List[float], alpha: float = 0.05) -> float:
    """
    Calculate empirical power from real data p-values.
    Power is the proportion of tests that rejected the null hypothesis (p < alpha).
    
    Args:
        real_p_values: List of observed p-values from real data.
        alpha: Significance threshold.
        
    Returns:
        Estimated power (float between 0 and 1).
    """
    if not real_p_values:
        return 0.0
    rejections = sum(1 for p in real_p_values if p < alpha)
    return rejections / len(real_p_values)

def calculate_validation_metrics(power_results_path: str = REAL_DATA_POWER_PATH) -> Dict[str, Any]:
    """
    Aggregate results from real_data_power.json and calculate summary statistics.
    
    This function implements T034:
    - Reads real_data_power.json
    - Calculates total datasets processed
    - Counts how many passed validation (e.g., KS distance <= 0.10)
    - Calculates average KS distance
    
    Args:
        power_results_path: Path to real_data_power.json.
        
    Returns:
        Dictionary with validation metrics:
        - total_datasets
        - passed_validation_count
        - avg_ks_distance
        - details: list of per-dataset metrics
    """
    if not os.path.exists(power_results_path):
        raise FileNotFoundError(f"Power results not found at {power_results_path}")
        
    with open(power_results_path, 'r') as f:
        data = json.load(f)
        
    # Handle both list and dict formats
    if isinstance(data, dict) and 'results' in data:
        results = data['results']
    elif isinstance(data, list):
        results = data
    else:
        # Assume single result wrapped in dict
        results = [data]
        
    total_datasets = len(results)
    passed_count = 0
    ks_distances = []
    details = []
    
    for item in results:
        ds_id = item.get('dataset_id', 'unknown')
        ks_dist = item.get('ks_distance', float('inf'))
        power_est = item.get('power_estimate', 0.0)
        
        # Validation passes if KS distance is <= 0.10 (as per T032 verification)
        passed = ks_dist <= 0.10
        if passed:
            passed_count += 1
            
        ks_distances.append(ks_dist)
        
        details.append({
            'dataset_id': ds_id,
            'ks_distance': ks_dist,
            'power_estimate': power_est,
            'passed_validation': passed
        })
        
    avg_ks = np.mean(ks_distances) if ks_distances else 0.0
    
    metrics = {
        'total_datasets': total_datasets,
        'passed_validation_count': passed_count,
        'avg_ks_distance': float(avg_ks),
        'details': details,
        'validation_timestamp': datetime.utcnow().isoformat()
    }
    
    return metrics

def save_validation_metrics(metrics: Dict[str, Any], output_path: str = VALIDATION_METRICS_PATH) -> None:
    """
    Save validation metrics to JSON file.
    
    Args:
        metrics: Dictionary of metrics to save.
        output_path: Path to output JSON file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)

def main():
    """
    Main entry point for T034.
    Aggregates real_data_power.json and writes validation_metrics.json.
    """
    import pandas as pd
    from datetime import datetime
    
    print("Starting T034: Calculating validation metrics...")
    
    try:
        # Load power results
        metrics = calculate_validation_metrics()
        
        # Save to file
        save_validation_metrics(metrics)
        
        print(f"Validation metrics saved to {VALIDATION_METRICS_PATH}")
        print(f"  Total datasets: {metrics['total_datasets']}")
        print(f"  Passed validation: {metrics['passed_validation_count']}")
        print(f"  Avg KS distance: {metrics['avg_ks_distance']:.4f}")
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Ensure that T032 (real_data_power.json) has been completed first.")
        raise
    except Exception as e:
        print(f"Error calculating validation metrics: {e}")
        raise

if __name__ == "__main__":
    main()
