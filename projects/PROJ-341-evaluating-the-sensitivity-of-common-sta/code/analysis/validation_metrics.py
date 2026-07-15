"""
Module to calculate validation metrics and KS statistics.
Compares real data p-value distributions against simulated predictions.
"""
import os
import json
import csv
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from scipy import stats

# Path constants
REAL_DATA_PVALUES_PATH = "data/simulation/real_data_pvalues.csv"
SIMULATED_PVALUES_PATH = "data/simulation/p_values_raw.csv"
REAL_DATA_POWER_PATH = "data/simulation/real_data_power.json"
VALIDATION_METRICS_PATH = "data/simulation/validation_metrics.json"

def load_simulated_pvalues_for_comparison() -> Dict[str, List[float]]:
    """
    Load simulated p-values grouped by test type and sample size.
    Returns a dictionary: { (test_type, sample_size): [p_values...] }
    """
    if not os.path.exists(SIMULATED_PVALUES_PATH):
        raise FileNotFoundError(f"Simulated p-values file not found: {SIMULATED_PVALUES_PATH}")

    data = {}
    with open(SIMULATED_PVALUES_PATH, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            test_type = row.get('test_type', '').strip()
            sample_size_str = row.get('sample_size', '').strip()
            p_value_str = row.get('p_value', '').strip()

            if not test_type or not sample_size_str or not p_value_str:
                continue

            try:
                sample_size = int(sample_size_str)
                p_value = float(p_value_str)
            except ValueError:
                continue

            key = (test_type, sample_size)
            if key not in data:
                data[key] = []
            data[key].append(p_value)

    return data

def load_real_data_pvalues_for_comparison() -> Dict[str, List[float]]:
    """
    Load real data p-values grouped by test type.
    Returns a dictionary: { test_type: [p_values...] }
    """
    if not os.path.exists(REAL_DATA_PVALUES_PATH):
        raise FileNotFoundError(f"Real data p-values file not found: {REAL_DATA_PVALUES_PATH}")

    data = {}
    with open(REAL_DATA_PVALUES_PATH, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            test_type = row.get('test_type', '').strip()
            p_value_str = row.get('p_value', '').strip()

            if not test_type or not p_value_str:
                continue

            try:
                p_value = float(p_value_str)
            except ValueError:
                continue

            if test_type not in data:
                data[test_type] = []
            data[test_type].append(p_value)

    return data

def calculate_real_data_power(real_pvalues: List[float], alpha: float = 0.05) -> float:
    """
    Calculate empirical power as the proportion of p-values < alpha.
    Note: For real data where ground truth is unknown, this is an estimate
    of the test's sensitivity in the observed context.
    """
    if not real_pvalues:
        return 0.0
    significant_count = sum(1 for p in real_pvalues if p < alpha)
    return significant_count / len(real_pvalues)

def calculate_ks_distance(simulated_pvalues: List[float], real_pvalues: List[float]) -> float:
    """
    Calculate the Kolmogorov-Smirnov distance between two distributions.
    Returns the KS statistic (D).
    """
    if not simulated_pvalues or not real_pvalues:
        return np.nan

    try:
        ks_stat, _ = stats.ks_2samp(simulated_pvalues, real_pvalues)
        return float(ks_stat)
    except Exception:
        return np.nan

def calculate_validation_metrics(alpha: float = 0.05) -> Dict[str, Any]:
    """
    Calculate validation metrics comparing real data to simulation.
    Returns a dictionary with KS distances and power estimates per test type.
    """
    simulated_data = load_simulated_pvalues_for_comparison()
    real_data = load_real_data_pvalues_for_comparison()

    metrics = {
        "alpha": alpha,
        "test_types": {},
        "summary": {
            "total_tests_compared": 0,
            "max_ks_distance": 0.0,
            "avg_ks_distance": 0.0,
            "ks_distances": []
        }
    }

    # We need to match real data test types with simulated data.
    # Since real data might have varying sample sizes, we aggregate simulated data
    # across sample sizes for the same test type to get a distribution.
    # Alternatively, we can compare against the most relevant sample size bin.
    # For this implementation, we aggregate simulated p-values by test type
    # to create a reference distribution.

    simulated_by_test = {}
    for (test_type, _), pvals in simulated_data.items():
        if test_type not in simulated_by_test:
            simulated_by_test[test_type] = []
        simulated_by_test[test_type].extend(pvals)

    all_ks_distances = []

    for test_type, real_pvals in real_data.items():
        if test_type not in simulated_by_test:
            continue

        sim_pvals = simulated_by_test[test_type]

        # Calculate KS distance
        ks_dist = calculate_ks_distance(sim_pvals, real_pvals)

        # Calculate real data power
        real_power = calculate_real_data_power(real_pvals, alpha)

        # Calculate simulated power (proportion < alpha in simulation)
        sim_power = sum(1 for p in sim_pvals if p < alpha) / len(sim_pvals) if sim_pvals else 0.0

        metrics["test_types"][test_type] = {
            "ks_distance": ks_dist,
            "real_data_power": real_power,
            "simulated_power": sim_power,
            "real_data_n": len(real_pvals),
            "simulated_data_n": len(sim_pvals),
            "ks_distance_pass": ks_dist <= 0.10 if not np.isnan(ks_dist) else False
        }

        if not np.isnan(ks_dist):
            all_ks_distances.append(ks_dist)

    # Summary statistics
    metrics["summary"]["total_tests_compared"] = len(metrics["test_types"])
    if all_ks_distances:
        metrics["summary"]["max_ks_distance"] = float(max(all_ks_distances))
        metrics["summary"]["avg_ks_distance"] = float(np.mean(all_ks_distances))
        metrics["summary"]["ks_distances"] = all_ks_distances
        metrics["summary"]["overall_ks_pass"] = metrics["summary"]["max_ks_distance"] <= 0.10
    else:
        metrics["summary"]["overall_ks_pass"] = False

    return metrics

def save_validation_metrics(metrics: Dict[str, Any], output_path: str = VALIDATION_METRICS_PATH) -> str:
    """
    Save validation metrics to a JSON file.
    Returns the path to the saved file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    return output_path

def main():
    """
    Main entry point to calculate and save validation metrics.
    """
    print("Calculating validation metrics...")
    try:
        metrics = calculate_validation_metrics(alpha=0.05)
        output_path = save_validation_metrics(metrics)
        print(f"Validation metrics saved to: {output_path}")
        print(f"Overall KS distance pass: {metrics['summary'].get('overall_ks_pass', False)}")
        print(f"Max KS distance: {metrics['summary'].get('max_ks_distance', 'N/A')}")
        return 0
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())