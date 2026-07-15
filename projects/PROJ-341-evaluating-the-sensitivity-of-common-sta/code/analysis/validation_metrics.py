"""
validation_metrics.py

Implements logic to calculate validation metrics and KS statistics comparing
simulated predictions against real-world dataset behavior.

This module fulfills Task T034: Save validation metrics and KS statistics to
data/simulation/validation_metrics.json.

It depends on:
- data/simulation/p_values_raw.csv (simulated p-values)
- data/simulation/real_data_pvalues.csv (real data p-values)
- data/simulation/real_data_power.json (bootstrapped power estimates from T032)
"""

import os
import json
import csv
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from scipy import stats

# Constants
SIMULATED_PVALUES_PATH = "data/simulation/p_values_raw.csv"
REAL_DATA_PVALUES_PATH = "data/simulation/real_data_pvalues.csv"
REAL_DATA_POWER_PATH = "data/simulation/real_data_power.json"
OUTPUT_PATH = "data/simulation/validation_metrics.json"


def load_simulated_pvalues_for_comparison(test_type: Optional[str] = None) -> Dict[str, List[float]]:
    """
    Load simulated p-values from p_values_raw.csv, optionally filtering by test type.

    Args:
        test_type: Optional filter for test type (e.g., 't-test', 'anova', 'chi-squared').

    Returns:
        Dictionary mapping (sample_size, effect_size) to list of p-values.
    """
    if not os.path.exists(SIMULATED_PVALUES_PATH):
        raise FileNotFoundError(f"Simulated p-values file not found: {SIMULATED_PVALUES_PATH}")

    p_values_by_condition = {}

    with open(SIMULATED_PVALUES_PATH, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if test_type and row['test_type'] != test_type:
                continue

            n = int(row['sample_size'])
            effect_size = float(row['effect_size'])
            p_value = float(row['p_value'])

            key = (n, effect_size)
            if key not in p_values_by_condition:
                p_values_by_condition[key] = []
            p_values_by_condition[key].append(p_value)

    return p_values_by_condition


def load_real_data_pvalues() -> Dict[str, List[float]]:
    """
    Load p-values from real-world dataset analysis.

    Returns:
        Dictionary mapping test_type to list of p-values.
    """
    if not os.path.exists(REAL_DATA_PVALUES_PATH):
        raise FileNotFoundError(f"Real data p-values file not found: {REAL_DATA_PVALUES_PATH}")

    p_values_by_test = {}

    with open(REAL_DATA_PVALUES_PATH, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            test_type = row['test_type']
            p_value = float(row['p_value'])

            if test_type not in p_values_by_test:
                p_values_by_test[test_type] = []
            p_values_by_test[test_type].append(p_value)

    return p_values_by_test


def calculate_real_data_power(real_p_values: List[float], alpha: float = 0.05) -> Dict[str, float]:
    """
    Calculate empirical power from real data p-values.

    Power is estimated as the proportion of tests that reject the null hypothesis
    (p < alpha). For real data, this is a heuristic estimate since ground truth
    is unknown.

    Args:
        real_p_values: List of p-values from real data tests.
        alpha: Significance threshold.

    Returns:
        Dictionary with 'empirical_power' and 'sample_size'.
    """
    if not real_p_values:
        return {'empirical_power': np.nan, 'sample_size': 0}

    rejections = sum(1 for p in real_p_values if p < alpha)
    power = rejections / len(real_p_values)

    return {
        'empirical_power': float(power),
        'sample_size': len(real_p_values)
    }


def calculate_ks_distance(simulated_pvalues: List[float], real_p_values: List[float]) -> Dict[str, float]:
    """
    Calculate Kolmogorov-Smirnov distance between simulated and real p-value distributions.

    The KS statistic measures the maximum distance between the empirical CDFs of
    the two samples. A value close to 0 indicates similar distributions.

    Args:
        simulated_pvalues: List of p-values from simulation.
        real_p_values: List of p-values from real data.

    Returns:
        Dictionary with 'ks_statistic' and 'p_value' (KS test p-value).
    """
    if not simulated_pvalues or not real_p_values:
        return {'ks_statistic': np.nan, 'p_value': np.nan, 'note': 'insufficient_data'}

    ks_stat, p_val = stats.ks_2samp(simulated_pvalues, real_p_values)

    return {
        'ks_statistic': float(ks_stat),
        'p_value': float(p_val),
        'note': 'ks_test_performed'
    }


def calculate_validation_metrics(alpha: float = 0.05) -> Dict[str, Any]:
    """
    Calculate comprehensive validation metrics comparing simulation to real data.

    This function:
    1. Loads simulated and real p-values
    2. Loads bootstrapped power estimates from T032
    3. Calculates KS distances for each test type
    4. Compares empirical power estimates
    5. Generates a summary validation status

    Args:
        alpha: Significance threshold for power calculations.

    Returns:
        Dictionary containing all validation metrics and status.
    """
    metrics = {
        'timestamp': str(np.datetime64('now')),
        'alpha': alpha,
        'test_types': {},
        'summary': {}
    }

    # Load real data power estimates (from T032)
    real_power_data = {}
    if os.path.exists(REAL_DATA_POWER_PATH):
        with open(REAL_DATA_POWER_PATH, 'r') as f:
            real_power_data = json.load(f)

    # Load real data p-values
    real_p_values_by_test = load_real_data_pvalues()

    # Analyze each test type
    for test_type in ['t-test', 'anova', 'chi-squared']:
        test_metrics = {
            'ks_distance': None,
            'power_comparison': None,
            'validation_status': None
        }

        # Get real p-values for this test
        if test_type not in real_p_values_by_test:
            test_metrics['validation_status'] = 'no_real_data'
            metrics['test_types'][test_type] = test_metrics
            continue

        real_pvals = real_p_values_by_test[test_type]

        # Get simulated p-values for comparable conditions (small sample sizes)
        # Focus on n < 30 where sensitivity is highest
        sim_pvals = []
        sim_pvalues_all = load_simulated_pvalues_for_comparison(test_type)
        for (n, effect), p_list in sim_pvalues_all.items():
            if n < 30:  # Small sample regime
                sim_pvals.extend(p_list)

        if not sim_pvals:
            test_metrics['validation_status'] = 'no_simulated_data'
            metrics['test_types'][test_type] = test_metrics
            continue

        # Calculate KS distance
        ks_result = calculate_ks_distance(sim_pvals, real_pvals)
        test_metrics['ks_distance'] = ks_result

        # Calculate power for real data
        real_power = calculate_real_data_power(real_pvals, alpha)

        # Get simulated power (proportion of rejections in simulation)
        sim_rejections = sum(1 for p in sim_pvals if p < alpha)
        sim_power = sim_rejections / len(sim_pvals) if sim_pvals else 0.0

        # Compare powers
        power_diff = abs(real_power['empirical_power'] - sim_power)
        test_metrics['power_comparison'] = {
            'real_power': real_power['empirical_power'],
            'simulated_power': sim_power,
            'difference': power_diff,
            'ks_threshold_met': ks_result['ks_statistic'] <= 0.10 if not np.isnan(ks_result['ks_statistic']) else False
        }

        # Determine validation status
        if power_diff <= 0.10 and (not np.isnan(ks_result['ks_statistic']) and ks_result['ks_statistic'] <= 0.10):
            test_metrics['validation_status'] = 'PASS'
        elif power_diff <= 0.20:
            test_metrics['validation_status'] = 'WARNING'
        else:
            test_metrics['validation_status'] = 'FAIL'

        metrics['test_types'][test_type] = test_metrics

    # Generate summary
    pass_count = sum(1 for m in metrics['test_types'].values() if m.get('validation_status') == 'PASS')
    total_count = len(metrics['test_types'])

    metrics['summary'] = {
        'total_tests': total_count,
        'passed': pass_count,
        'failed': total_count - pass_count,
        'overall_status': 'PASS' if pass_count == total_count and total_count > 0 else 'PARTIAL' if pass_count > 0 else 'FAIL',
        'ks_threshold': 0.10,
        'power_threshold': 0.10
    }

    return metrics


def save_validation_metrics(metrics: Dict[str, Any], output_path: Optional[str] = None) -> str:
    """
    Save validation metrics to JSON file.

    Args:
        metrics: Dictionary of metrics to save.
        output_path: Path for output file (default: data/simulation/validation_metrics.json).

    Returns:
        Path to the saved file.
    """
    if output_path is None:
        output_path = OUTPUT_PATH

    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    return output_path

    return output_path


def main():
    """
    Main entry point for T034: Calculate and save validation metrics.

    This function:
    1. Loads necessary data files (simulated p-values, real data p-values, power estimates)
    2. Calculates KS distances and power comparisons
    3. Generates validation status for each test type
    4. Saves results to data/simulation/validation_metrics.json
    """
    print("Starting validation metrics calculation (T034)...")

    try:
        # Calculate metrics
        metrics = calculate_validation_metrics(alpha=0.05)

        # Save to file
        output_path = save_validation_metrics(metrics)

        print(f"Validation metrics saved to: {output_path}")
        print(f"Overall status: {metrics['summary']['overall_status']}")
        print(f"Tests passed: {metrics['summary']['passed']}/{metrics['summary']['total_tests']}")

        return 0

    except FileNotFoundError as e:
        print(f"ERROR: Required data file missing: {e}")
        print("Ensure T016 (p_values_raw.csv), T031 (real_data_pvalues.csv), and T032 (real_data_power.json) are complete.")
        return 1
    except Exception as e:
        print(f"ERROR: Failed to calculate validation metrics: {e}")
        raise


if __name__ == "__main__":
    exit(main())
