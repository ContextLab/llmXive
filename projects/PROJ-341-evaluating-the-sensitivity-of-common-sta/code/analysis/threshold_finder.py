"""
Threshold identification and reliability analysis.

Computes binomial confidence intervals (Wilson score) for error rates
and identifies sample size thresholds where error rates deviate from
nominal alpha or power drops below 0.80.
"""
import os
import json
import csv
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from scipy import stats


def wilson_score_interval(
    successes: float, 
    n: float, 
    confidence: float = 0.95
) -> Tuple[float, float]:
    """
    Calculate Wilson score interval for binomial proportion.
    
    Args:
        successes: Number of successes (e.g., Type I errors)
        n: Total number of trials
        confidence: Confidence level (default 0.95)
        
    Returns:
        Tuple of (lower_bound, upper_bound)
    """
    if n == 0:
        return 0.0, 0.0
        
    z = stats.norm.ppf(1 - (1 - confidence) / 2)
    p_hat = successes / n
    
    denominator = 1 + z**2 / n
    center = (p_hat + z**2 / (2 * n)) / denominator
    margin = z * np.sqrt((p_hat * (1 - p_hat) + z**2 / (4 * n)) / n) / denominator
    
    return max(0.0, center - margin), min(1.0, center + margin)


def calculate_confidence_intervals(
    error_rates: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Add Wilson score confidence intervals to error rate records.
    
    Args:
        error_rates: List of dicts with keys: 
            - test_type, effect_size, sample_size, error_rate, n_simulations
            
    Returns:
        List with added keys: ci_lower, ci_upper
    """
    result = []
    for record in error_rates:
        new_record = record.copy()
        n = record.get('n_simulations', 10000)
        successes = record['error_rate'] * n
        
        lower, upper = wilson_score_interval(successes, n)
        new_record['ci_lower'] = lower
        new_record['ci_upper'] = upper
        result.append(new_record)
        
    return result


def load_error_rates(filepath: str) -> List[Dict[str, Any]]:
    """
    Load aggregated error rates from CSV.
    
    Args:
        filepath: Path to error_rates_summary.csv
        
    Returns:
        List of dictionaries with error rate data
    """
    if not os.path.exists(filepath):
        logger = get_logger("threshold_finder")
        logger.warning("load_error_rates", filepath=filepath, error="File not found")
        return []
        
    results = []
    with open(filepath, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            record = {
                'test_type': row['test_type'],
                'effect_size': float(row['effect_size']),
                'sample_size': int(row['sample_size']),
                'hypothesis': row['hypothesis'],
                'error_rate': float(row['error_rate']),
                'n_simulations': int(row.get('n_simulations', 10000))
            }
            results.append(record)
            
    return results


def find_type_i_threshold(
    error_rates_with_ci: List[Dict[str, Any]],
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Identify the smallest sample size where the Type I error 
    lower confidence interval bound exceeds alpha.
    
    Args:
        error_rates_with_ci: List of error rate records with CI bounds
        alpha: Nominal significance level (default 0.05)
        
    Returns:
        Dict with threshold info or None if not found
    """
    # Filter for Type I error (hypothesis = 'null_true')
    type_i_errors = [
        r for r in error_rates_with_ci 
        if r['hypothesis'] == 'null_true'
    ]
    
    # Group by test_type and effect_size
    grouped = {}
    for record in type_i_errors:
        key = (record['test_type'], record['effect_size'])
        if key not in grouped:
            grouped[key] = []
        grouped[key].append(record)
    
    thresholds = {}
    for (test_type, effect_size), records in grouped.items():
        # Sort by sample size
        records_sorted = sorted(records, key=lambda x: x['sample_size'])
        
        threshold_n = None
        for record in records_sorted:
            if record['ci_lower'] > alpha:
                threshold_n = record['sample_size']
                break
        
        if threshold_n is not None:
          thresholds[(test_type, effect_size)] = {
              'test_type': test_type,
              'effect_size': effect_size,
              'threshold_n': threshold_n,
              'threshold_type': 'type_i_inflation'
          }
    
    return thresholds


def find_power_threshold(
    error_rates_with_ci: List[Dict[str, Any]],
    power_target: float = 0.80,
    min_consecutive: int = 3
) -> Dict[str, Any]:
    """
    Identify the smallest n where power CI remains < power_target 
    for min_consecutive increments.
    
    Args:
        error_rates_with_ci: List of error rate records with CI bounds
        power_target: Target power level (default 0.80)
        min_consecutive: Minimum consecutive increments below target (default 3)
        
    Returns:
        Dict with threshold info or empty dict if not found
    """
    # Filter for Type II error (hypothesis = 'alt_true')
    # Power = 1 - Type II error rate
    type_ii_errors = [
        r for r in error_rates_with_ci 
        if r['hypothesis'] == 'alt_true'
    ]
    
    # Group by test_type and effect_size
    grouped = {}
    for record in type_ii_errors:
        key = (record['test_type'], record['effect_size'])
        if key not in grouped:
            grouped[key] = []
        grouped[key].append(record)
    
    thresholds = {}
    for (test_type, effect_size), records in grouped.items():
        # Sort by sample size
        records_sorted = sorted(records, key=lambda x: x['sample_size'])
        
        threshold_n = None
        consecutive_below = 0
        
        for record in records_sorted:
            # Power = 1 - Type II error rate
            # We want power < target, which means error_rate > (1 - target)
            power = 1.0 - record['error_rate']
            power_upper = 1.0 - record['ci_lower']  # Upper bound of power CI
            
            if power_upper < power_target:
                consecutive_below += 1
                if consecutive_below >= min_consecutive and threshold_n is None:
                    threshold_n = record['sample_size']
            else:
                consecutive_below = 0
        
        if threshold_n is not None:
            thresholds[(test_type, effect_size)] = {
                'test_type': test_type,
                'effect_size': effect_size,
                'threshold_n': threshold_n,
                'threshold_type': 'power_deficit',
                'power_target': power_target
            }
    
    return thresholds


def save_thresholds(
    thresholds: Dict[str, Any],
    filepath: str = "data/simulation/thresholds.json"
) -> None:
    """
    Save threshold metrics to JSON file.
    
    Args:
        thresholds: Dictionary of threshold results
        filepath: Output path for JSON file
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    # Convert tuple keys to strings for JSON serialization
    serializable = {}
    for key, value in thresholds.items():
        if isinstance(key, tuple):
            str_key = f"{key[0]}_{key[1]}"
        else:
            str_key = str(key)
        serializable[str_key] = value
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(serializable, f, indent=2)


def main() -> None:
    """
    Main entry point for threshold analysis.
    
    Loads error rates, calculates confidence intervals,
    identifies thresholds, and saves results to JSON.
    """
    print("Loading error rates from data/simulation/error_rates_summary.csv...")
    try:
        error_rates = load_error_rates()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please run the simulation first to generate error_rates_summary.csv")
        return
    
    print(f"Loaded {len(error_rates)} error rate records.")
    
    print("Calculating confidence intervals...")
    error_rates_with_ci = calculate_confidence_intervals(error_rates)
    
    print("Identifying Type I error thresholds...")
    type_i_thresholds = find_type_i_threshold(error_rates_with_ci)
    
    print("Identifying power thresholds...")
    power_thresholds = find_power_threshold(error_rates_with_ci)
    
    # Combine all thresholds
    all_thresholds = {}
    all_thresholds.update(type_i_thresholds)
    all_thresholds.update(power_thresholds)
    
    output_path = "data/simulation/thresholds.json"
    print(f"Saving {len(all_thresholds)} thresholds to {output_path}...")
    save_thresholds(all_thresholds, output_path)
    
    print("Threshold analysis complete.")
    print(f"Output written to: {output_path}")


if __name__ == "__main__":
    from datetime import datetime
    main()
