import os
import json
import csv
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from scipy import stats

def wilson_score_interval(count_success: int, n_total: int, confidence: float = 0.95) -> Tuple[float, float]:
    """
    Calculate the Wilson score interval for a proportion.
    
    Args:
        count_success: Number of successes (e.g., rejections under null)
        n_total: Total number of trials
        confidence: Confidence level (default 0.95)
        
    Returns:
        Tuple of (lower_bound, upper_bound)
    """
    if n_total == 0:
        return 0.0, 0.0
        
    z = stats.norm.ppf(1 - (1 - confidence) / 2)
    p_hat = count_success / n_total
    
    denominator = 1 + z**2 / n_total
    center = (p_hat + z**2 / (2 * n_total)) / denominator
    margin = (z / denominator) * np.sqrt(p_hat * (1 - p_hat) / n_total + z**2 / (4 * n_total**2))
    
    lower = max(0.0, center - margin)
    upper = min(1.0, center + margin)
    
    return lower, upper

def calculate_confidence_intervals(error_rates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Add Wilson score confidence intervals to error rate records.
    
    Args:
        error_rates: List of dicts with 'n', 'test_type', 'effect_size', 'error_rate', 'n_iterations'
        
    Returns:
        Updated list with 'ci_lower' and 'ci_upper' fields
    """
    for record in error_rates:
        n_iter = record.get('n_iterations', 10000)
        # Reconstruct count_success from error_rate and n_iterations
        count_success = int(round(record['error_rate'] * n_iter))
        lower, upper = wilson_score_interval(count_success, n_iter)
        record['ci_lower'] = lower
        record['ci_upper'] = upper
    return error_rates

def load_error_rates(filepath: str = "data/simulation/error_rates_summary.csv") -> List[Dict[str, Any]]:
    """
    Load error rates from CSV file.
    
    Args:
        filepath: Path to the CSV file
        
    Returns:
        List of dictionaries containing error rate data
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Error rates file not found: {filepath}")
        
    records = []
    with open(filepath, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            record = {
                'n': int(row['sample_size']),
                'test_type': row['test_type'],
                'effect_size': float(row['effect_size']),
                'hypothesis': row['hypothesis'],
                'error_rate': float(row['error_rate']),
                'n_iterations': int(row['n_iterations'])
            }
            records.append(record)
    return records

def find_type_i_threshold(error_rates: List[Dict[str, Any]], alpha: float = 0.05) -> Dict[str, Any]:
    """
    Find the smallest sample size where Type I error lower CI bound > alpha.
    
    Args:
        error_rates: List of error rate records with CI bounds
        alpha: Significance level (default 0.05)
        
    Returns:
        Dictionary with threshold details or None if not found
    """
    # Filter for Type I error (null hypothesis true)
    type_i_records = [r for r in error_rates if r['hypothesis'] == 'null_true']
    
    # Group by test_type and effect_size
    thresholds = {}
    for test_type in set(r['test_type'] for r in type_i_records):
        for effect_size in set(r['effect_size'] for r in type_i_records if r['test_type'] == test_type):
            subset = [r for r in type_i_records if r['test_type'] == test_type and r['effect_size'] == effect_size]
            subset.sort(key=lambda x: x['n'])
            
            found_n = None
            for record in subset:
                if record['ci_lower'] > alpha:
                    found_n = record['n']
                    break
                    
            if found_n is not None:
                key = f"{test_type}_{effect_size}"
                thresholds[key] = {
                    'test_type': test_type,
                    'effect_size': effect_size,
                    'threshold_n': found_n,
                    'threshold_type': 'type_i_error_inflated',
                    'alpha': alpha
                }
                
    return thresholds

def find_power_threshold(error_rates: List[Dict[str, Any]], power_target: float = 0.80, consecutive: int = 3) -> Dict[str, Any]:
    """
    Find the smallest sample size where power CI remains < target for consecutive increments.
    
    Args:
        error_rates: List of error rate records with CI bounds
        power_target: Target power level (default 0.80)
        consecutive: Number of consecutive increments required (default 3)
        
    Returns:
        Dictionary with threshold details or empty dict if not found
    """
    # Filter for Type II error (alternative hypothesis true) - power = 1 - Type II error rate
    type_ii_records = [r for r in error_rates if r['hypothesis'] == 'alt_true']
    
    thresholds = {}
    for test_type in set(r['test_type'] for r in type_ii_records):
        for effect_size in set(r['effect_size'] for r in type_ii_records if r['test_type'] == test_type):
            subset = [r for r in type_ii_records if r['test_type'] == test_type and r['effect_size'] == effect_size]
            subset.sort(key=lambda x: x['n'])
            
            # Calculate power = 1 - error_rate (for Type II error)
            # We want power < target, which means error_rate > (1 - target)
            power_threshold = 1 - power_target
            
            found_n = None
            consecutive_count = 0
            
            for i, record in enumerate(subset):
                # Power = 1 - Type II error rate
                # But our error_rate for alt_true is actually Type II error rate
                # So power = 1 - record['error_rate']
                power = 1 - record['error_rate']
                ci_upper_power = 1 - record['ci_lower']  # Upper bound of power corresponds to lower bound of error
                
                # Check if power CI upper bound is < target
                # Actually, we want to check if the entire CI is below target
                # So we check if ci_upper_power < power_target
                if ci_upper_power < power_target:
                    consecutive_count += 1
                    if consecutive_count >= consecutive:
                        found_n = record['n']
                        break
                else:
                    consecutive_count = 0
                    
            if found_n is not None:
                key = f"{test_type}_{effect_size}"
                thresholds[key] = {
                    'test_type': test_type,
                    'effect_size': effect_size,
                    'threshold_n': found_n,
                    'threshold_type': 'power_below_target',
                    'power_target': power_target,
                    'consecutive_increments': consecutive
                }
                
    return thresholds

def save_thresholds(thresholds: Dict[str, Any], filepath: str = "data/simulation/thresholds.json") -> None:
    """
    Save threshold metrics to JSON file.
    
    Args:
        thresholds: Dictionary of threshold results
        filepath: Output file path
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    output = {
        'generated_at': str(np.datetime64('now')),
        'thresholds': list(thresholds.values())
    }
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)

def main():
    """Main entry point for threshold analysis."""
    print("Starting threshold analysis...")
    
    # Load error rates
    try:
        error_rates = load_error_rates("data/simulation/error_rates_summary.csv")
        print(f"Loaded {len(error_rates)} error rate records")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please run the simulation first to generate error_rates_summary.csv")
        return
    
    # Calculate confidence intervals
    error_rates = calculate_confidence_intervals(error_rates)
    print(f"Calculated confidence intervals for {len(error_rates)} records")
    
    # Find Type I error thresholds
    type_i_thresholds = find_type_i_threshold(error_rates)
    print(f"Found {len(type_i_thresholds)} Type I error thresholds")
    
    # Find power thresholds
    power_thresholds = find_power_threshold(error_rates)
    print(f"Found {len(power_thresholds)} power thresholds")
    
    # Combine all thresholds
    all_thresholds = {**type_i_thresholds, **power_thresholds}
    
    # Save to JSON
    save_thresholds(all_thresholds, "data/simulation/thresholds.json")
    print("Saved thresholds to data/simulation/thresholds.json")
    
    # Print summary
    print("\n=== Threshold Summary ===")
    for key, value in all_thresholds.items():
        print(f"{value['test_type']} (effect={value['effect_size']}): n={value['threshold_n']} [{value['threshold_type']}]")

if __name__ == "__main__":
    main()