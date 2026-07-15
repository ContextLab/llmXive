import os
import json
import csv
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from scipy import stats
from code.simulation.logging_config import get_logger

# Ensure imports align with the provided API surface
# The API surface lists: wilson_score_interval, calculate_confidence_intervals, load_error_rates, find_type_i_threshold, find_power_threshold, save_thresholds, main

def wilson_score_interval(count: int, n: int, confidence: float = 0.95) -> Tuple[float, float]:
    """
    Calculate the Wilson score interval for a binomial proportion.
    
    Args:
        count: Number of successes (e.g., number of rejections)
        n: Total number of trials (iterations)
        confidence: Confidence level (default 0.95)
    
    Returns:
        Tuple of (lower_bound, upper_bound).
    """
    if n == 0:
        return 0.0, 0.0
    
    z = stats.norm.ppf(1 - (1 - confidence) / 2)
    p_hat = count / n
    
    denominator = 1 + z**2 / n
    center = (p_hat + z**2 / (2 * n)) / denominator
    margin = (z / denominator) * np.sqrt(p_hat * (1 - p_hat) / n + z**2 / (4 * n**2))
    
    lower = max(0.0, center - margin)
    upper = min(1.0, center + margin)
    
    return lower, upper

def calculate_confidence_intervals(error_rates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Calculate Wilson score confidence intervals for all error rates.
    
    Args:
        error_rates: List of dicts containing 'n', 'test_type', 'effect_size', 
                     'type1_rejections', 'type2_rejections', 'total_iterations'
    
    Returns:
        List of dicts with added 'type1_ci_lower', 'type1_ci_upper', 
        'type2_ci_lower', 'type2_ci_upper'
    """
    for row in error_rates:
        n_iter = row.get('total_iterations', 0)
        if n_iter == 0:
            row['type1_ci_lower'] = 0.0
            row['type1_ci_upper'] = 0.0
            row['type2_ci_lower'] = 0.0
            row['type2_ci_upper'] = 0.0
            continue
        
        # Type I error CI
        t1_count = row.get('type1_rejections', 0)
        t1_lower, t1_upper = wilson_score_interval(t1_count, n_iter)
        row['type1_ci_lower'] = t1_lower
        row['type1_ci_upper'] = t1_upper
        
        # Type II error CI (or Power CI: 1 - Type II)
        t2_count = row.get('type2_rejections', 0)
        t2_lower, t2_upper = wilson_score_interval(t2_count, n_iter)
        row['type2_ci_lower'] = t2_lower
        row['type2_ci_upper'] = t2_upper
        
        # Power = 1 - Type II error rate
        # Power CI: [1 - t2_upper, 1 - t2_lower]
        row['power_ci_lower'] = 1.0 - t2_upper
        row['power_ci_upper'] = 1.0 - t2_lower
    
    return error_rates

def load_error_rates(filepath: str) -> List[Dict[str, Any]]:
    """
    Load error rates from CSV file.
    
    Args:
        filepath: Path to the CSV file (e.g., data/simulation/error_rates_summary.csv)
    
    Returns:
        List of dictionaries containing error rate data
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Error rates file not found: {filepath}")
    
    results = []
    with open(filepath, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric fields
            processed_row = {}
            for key, value in row.items():
                if key in ['n', 'total_iterations', 'type1_rejections', 'type2_rejections']:
                    processed_row[key] = int(value) if value else 0
                elif key in ['type1_error_rate', 'type2_error_rate', 'power']:
                    processed_row[key] = float(value) if value else 0.0
                else:
                    processed_row[key] = value
            results.append(processed_row)
    
    return results

def find_type_i_threshold(error_rates: List[Dict[str, Any]], alpha: float = 0.05) -> Optional[int]:
    """
    Identify the smallest sample size where the Type I error lower CI bound exceeds alpha.
    
    Args:
        error_rates: List of error rate data with confidence intervals
        alpha: Significance level threshold (default 0.05)
    
    Returns:
        The smallest n where Type I error lower CI > alpha, or None if not found
    """
    # Sort by sample size
    sorted_data = sorted(error_rates, key=lambda x: x['n'])
    
    for row in sorted_data:
        n = row['n']
        # Only consider cases where null hypothesis is true (effect_size == 0 or similar)
        # Typically effect_size is 0 for Type I error
        if row.get('effect_size') == 0.0 or row.get('effect_size') == '0.0' or row.get('effect_size') == 0:
            ci_lower = row.get('type1_ci_lower', 0.0)
            if ci_lower > alpha:
                return n
    
    return None

def find_power_threshold(error_rates: List[Dict[str, Any]], power_target: float = 0.80, 
                         consecutive: int = 3) -> Optional[int]:
    """
    Identify the smallest n where power CI remains below target for consecutive increments.
    
    Args:
        error_rates: List of error rate data with confidence intervals
        power_target: Target power threshold (default 0.80)
        consecutive: Number of consecutive increments required (default 3)
    
    Returns:
        The smallest n where power CI upper bound < power_target for 'consecutive' increments,
        or None if not found
    """
    # Sort by sample size
    sorted_data = sorted(error_rates, key=lambda x: x['n'])
    
    consecutive_count = 0
    last_valid_n = None
    
    for row in sorted_data:
        n = row['n']
        effect_size = row.get('effect_size')
        
        # Only consider cases where alternative hypothesis is true (effect_size > 0)
        if effect_size is not None and float(effect_size) > 0:
            power_ci_upper = row.get('power_ci_upper', 0.0)
            
            if power_ci_upper < power_target:
                consecutive_count += 1
                if consecutive_count >= consecutive:
                    return n
            else:
                consecutive_count = 0
    
    return None

def save_thresholds(thresholds: Dict[str, Any], filepath: str) -> None:
    """
    Save threshold metrics to a JSON file.
    
    Args:
        thresholds: Dictionary containing threshold metrics
        filepath: Path to save the JSON file (e.g., data/simulation/thresholds.json)
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(thresholds, f, indent=2)

def main():
    """
    Main function to compute and save threshold metrics.
    
    This function:
    1. Loads error rates from data/simulation/error_rates_summary.csv
    2. Calculates confidence intervals for all error rates
    3. Identifies Type I error threshold (where lower CI > 0.05)
    4. Identifies power threshold (where power < 0.80 for 3 consecutive n)
    5. Saves results to data/simulation/thresholds.json
    """
    input_file = 'data/simulation/error_rates_summary.csv'
    output_file = 'data/simulation/thresholds.json'
    
    print(f"Loading error rates from {input_file}...")
    try:
        error_rates = load_error_rates(input_file)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please ensure that data/simulation/error_rates_summary.csv exists.")
        return
    
    print(f"Calculating confidence intervals for {len(error_rates)} data points...")
    error_rates_with_ci = calculate_confidence_intervals(error_rates)
    
    # Group by test_type and effect_size to find thresholds for each combination
    test_types = set(row['test_type'] for row in error_rates_with_ci)
    effect_sizes = set(row['effect_size'] for row in error_rates_with_ci)
    
    thresholds = {
        'metadata': {
            'source_file': input_file,
            'alpha': 0.05,
            'power_target': 0.80,
            'consecutive_threshold': 3
        },
        'thresholds': []
    }
    
    for test_type in test_types:
        for effect_size in effect_sizes:
            # Filter data for this test type and effect size
            filtered_data = [
                row for row in error_rates_with_ci 
                if row['test_type'] == test_type and str(row['effect_size']) == str(effect_size)
            ]
            
            if not filtered_data:
                continue
            
            # Find Type I error threshold (only for effect_size == 0)
            type_i_threshold = None
            if float(effect_size) == 0.0:
                type_i_threshold = find_type_i_threshold(filtered_data, alpha=0.05)
            
            # Find power threshold (only for effect_size > 0)
            power_threshold = None
            if float(effect_size) > 0.0:
                power_threshold = find_power_threshold(filtered_data, power_target=0.80, consecutive=3)
            
            threshold_entry = {
                'test_type': test_type,
                'effect_size': float(effect_size),
                'type_i_threshold': type_i_threshold,
                'power_threshold': power_threshold
            }
            thresholds['thresholds'].append(threshold_entry)
    
    print(f"Saving threshold metrics to {output_file}...")
    save_thresholds(thresholds, output_file)
    print(f"Threshold metrics saved successfully.")
    
    # Print summary
    print("\nThreshold Summary:")
    for entry in thresholds['thresholds']:
        print(f"  {entry['test_type']} (effect_size={entry['effect_size']}):")
        if entry['type_i_threshold'] is not None:
            print(f"    - Type I error threshold: n = {entry['type_i_threshold']}")
        if entry['power_threshold'] is not None:
            print(f"    - Power threshold: n = {entry['power_threshold']}")

if __name__ == '__main__':
    main()