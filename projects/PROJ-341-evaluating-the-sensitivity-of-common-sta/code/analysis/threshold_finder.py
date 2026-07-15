import os
import json
import csv
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from scipy import stats

def wilson_score_interval(successes: float, trials: float, z: float = 1.96) -> Tuple[float, float]:
    """
    Calculate the Wilson score interval for a binomial proportion.
    
    Args:
        successes: Number of successes (e.g., Type I errors or Power events)
        trials: Total number of trials (iterations)
        z: Z-score for confidence level (default 1.96 for 95%)
    
    Returns:
        Tuple of (lower_bound, upper_bound)
    """
    if trials == 0:
        return 0.0, 0.0
    
    p_hat = successes / trials
    denominator = 1 + (z ** 2) / trials
    center = (p_hat + (z ** 2) / (2 * trials)) / denominator
    margin = (z / denominator) * np.sqrt((p_hat * (1 - p_hat) / trials) + (z ** 2) / (4 * trials ** 2))
    
    return max(0.0, center - margin), min(1.0, center + margin)

def calculate_confidence_intervals(error_rates_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Calculate Wilson score confidence intervals for all error rates.
    
    Args:
        error_rates_data: List of dicts with 'test_type', 'sample_size', 'effect_size', 
                         'error_rate', 'num_successes', 'num_trials'
    
    Returns:
        List of dicts with added 'ci_lower' and 'ci_upper' keys
    """
    results = []
    for row in error_rates_data:
        successes = row.get('num_successes', 0)
        trials = row.get('num_trials', 1)
        
        if trials > 0:
            lower, upper = wilson_score_interval(successes, trials)
        else:
            lower, upper = 0.0, 0.0
        
        row['ci_lower'] = lower
        row['ci_upper'] = upper
        results.append(row)
    
    return results

def find_type_i_threshold(error_rates_with_ci: List[Dict[str, Any]], alpha: float = 0.05) -> List[Dict[str, Any]]:
    """
    Identify the smallest sample size where Type I error lower CI bound > alpha.
    
    Args:
        error_rates_with_ci: Data with calculated confidence intervals
        alpha: Nominal significance level (default 0.05)
    
    Returns:
        List of threshold findings
    """
    thresholds = []
    
    # Filter for Type I error (H0 true, effect_size == 0 or null hypothesis)
    # Assuming effect_size=0 indicates null hypothesis for Type I error
    type_i_data = [r for r in error_rates_with_ci if r.get('hypothesis_state', 'null') == 'null' or abs(r.get('effect_size', 0)) < 1e-6]
    
    # Group by test type and effect size (though effect size should be 0 for Type I)
    groups = {}
    for row in type_i_data:
        key = (row['test_type'], row.get('effect_size', 0))
        if key not in groups:
            groups[key] = []
        groups[key].append(row)
    
    for (test_type, effect_size), rows in groups.items():
        # Sort by sample size
        sorted_rows = sorted(rows, key=lambda x: x['sample_size'])
        
        threshold_n = None
        for row in sorted_rows:
            if row['ci_lower'] > alpha:
                threshold_n = row['sample_size']
                break
        
        if threshold_n is not None:
            thresholds.append({
                'test_type': test_type,
                'effect_size': effect_size,
                'threshold_type': 'type_i_inflation',
                'identified_n': threshold_n,
                'description': f"Smallest n where Type I error lower CI > {alpha}"
            })
    
    return thresholds

def find_power_threshold(error_rates_with_ci: List[Dict[str, Any]], power_target: float = 0.80, consecutive_count: int = 3) -> List[Dict[str, Any]]:
    """
    Identify the smallest sample size where power CI remains < target for consecutive increments.
    
    Args:
        error_rates_with_ci: Data with calculated confidence intervals
        power_target: Target power level (default 0.80)
        consecutive_count: Number of consecutive increments required (default 3)
    
    Returns:
        List of threshold findings
    """
    thresholds = []
    
    # Filter for Type II error / Power analysis (H1 true)
    # Power = 1 - Type II error rate. We look for where power < 0.80
    # Assuming non-zero effect_size indicates alternative hypothesis
    power_data = [r for r in error_rates_with_ci if r.get('hypothesis_state', 'alt') == 'alt' or abs(r.get('effect_size', 0)) > 1e-6]
    
    # Group by test type and effect size
    groups = {}
    for row in power_data:
        key = (row['test_type'], row.get('effect_size', 0))
        if key not in groups:
            groups[key] = []
        groups[key].append(row)
    
    for (test_type, effect_size), rows in groups.items():
        sorted_rows = sorted(rows, key=lambda x: x['sample_size'])
        
        threshold_n = None
        consecutive_count_found = 0
        
        for i, row in enumerate(sorted_rows):
            # Power is 1 - Type II error rate (error_rate for alt hypothesis)
            # If error_rate > (1 - power_target), then power < power_target
            # Type II error rate = error_rate when H1 is true
            type_ii_rate = row['error_rate']
            power = 1 - type_ii_rate
            
            # Check if power CI upper bound is still below target
            # We want power < target, so if upper bound of power < target, we're confident it's low
            # But the task says "power CI remains < 0.80", meaning the entire interval is below
            # Actually, let's interpret as: the point estimate of power is < 0.80 for consecutive samples
            # Or more strictly: upper bound of power CI < 0.80
            
            # Power CI: [1 - row['ci_upper'], 1 - row['ci_lower']]
            # We want the upper bound of power < target
            power_upper = 1 - row['ci_lower']  # Since power = 1 - TypeII, and TypeII CI is [ci_lower, ci_upper]
            
            if power_upper < power_target:
                consecutive_count_found += 1
                if consecutive_count_found >= consecutive_count and threshold_n is None:
                    threshold_n = row['sample_size']
                    break
            else:
                consecutive_count_found = 0
        
        if threshold_n is not None:
            thresholds.append({
                'test_type': test_type,
                'effect_size': effect_size,
                'threshold_type': 'power_deficiency',
                'identified_n': threshold_n,
                'description': f"Smallest n where power CI upper bound < {power_target} for {consecutive_count} consecutive increments"
            })
    
    return thresholds

def load_error_rates(filepath: str = 'data/simulation/error_rates_summary.csv') -> List[Dict[str, Any]]:
    """Load error rates from CSV file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Error rates file not found: {filepath}")
    
    data = []
    with open(filepath, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert string values to appropriate types
            converted_row = {
                'test_type': row['test_type'],
                'sample_size': int(row['sample_size']),
                'effect_size': float(row['effect_size']),
                'hypothesis_state': row['hypothesis_state'],
                'error_rate': float(row['error_rate']),
                'num_successes': int(row['num_successes']),
                'num_trials': int(row['num_trials'])
            }
            data.append(converted_row)
    
    return data

def save_thresholds(thresholds: List[Dict[str, Any]], filepath: str = 'data/simulation/thresholds.json') -> None:
    """Save threshold metrics to JSON file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    output = {
        'thresholds': thresholds,
        'generated_at': str(datetime.now()),
        'total_thresholds_found': len(thresholds)
    }
    
    with open(filepath, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"Thresholds saved to {filepath}")

def main():
    """Main function to compute and save thresholds."""
    from datetime import datetime
    
    print("Loading error rates...")
    try:
        error_rates = load_error_rates('data/simulation/error_rates_summary.csv')
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please ensure User Story 1 has completed and generated error_rates_summary.csv")
        return
    
    print(f"Loaded {len(error_rates)} error rate records.")
    
    print("Calculating confidence intervals...")
    error_rates_with_ci = calculate_confidence_intervals(error_rates)
    
    print("Finding Type I error thresholds...")
    type_i_thresholds = find_type_i_threshold(error_rates_with_ci)
    print(f"Found {len(type_i_thresholds)} Type I thresholds.")
    
    print("Finding power thresholds...")
    power_thresholds = find_power_threshold(error_rates_with_ci)
    print(f"Found {len(power_thresholds)} power thresholds.")
    
    all_thresholds = type_i_thresholds + power_thresholds
    
    print("Saving thresholds...")
    save_thresholds(all_thresholds, 'data/simulation/thresholds.json')
    
    print("Threshold analysis complete.")

if __name__ == '__main__':
    main()