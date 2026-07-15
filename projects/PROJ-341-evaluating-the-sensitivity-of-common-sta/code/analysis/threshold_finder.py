import os
import json
import csv
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from scipy import stats

def wilson_score_interval(count_success: int, count_total: int, confidence: float = 0.95) -> Tuple[float, float]:
    """
    Calculate the Wilson score interval for a binomial proportion.
    
    Args:
        count_success: Number of successes (e.g., rejections)
        count_total: Total number of trials (iterations)
        confidence: Confidence level (default 0.95)
        
    Returns:
        Tuple of (lower_bound, upper_bound)
    """
    if count_total == 0:
        return 0.0, 0.0
        
    z = stats.norm.ppf(1 - (1 - confidence) / 2)
    p_hat = count_success / count_total
    
    denominator = 1 + (z**2) / count_total
    center = (p_hat + (z**2) / (2 * count_total)) / denominator
    margin = (z / denominator) * np.sqrt((p_hat * (1 - p_hat) / count_total) + (z**2) / (4 * count_total**2))
    
    return max(0.0, center - margin), min(1.0, center + margin)

def calculate_confidence_intervals(error_rates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Calculate Wilson score intervals for all error rate entries.
    
    Args:
        error_rates: List of dicts with keys: 'test_type', 'effect_size', 'sample_size', 'type_i_count', 'type_i_total', 'power_count', 'power_total'
        
    Returns:
        List of dicts with added CI bounds
    """
    results = []
    for entry in error_rates:
        new_entry = entry.copy()
        
        # Type I Error CI (when effect_size is 0 or near 0)
        if entry.get('effect_size', 0) == 0:
            lower, upper = wilson_score_interval(entry['type_i_count'], entry['type_i_total'])
            new_entry['type_i_lower_ci'] = lower
            new_entry['type_i_upper_ci'] = upper
        
        # Power CI (when effect_size > 0)
        if entry.get('effect_size', 0) > 0:
            power = entry['power_count'] / entry['power_total'] if entry['power_total'] > 0 else 0
            lower, upper = wilson_score_interval(entry['power_count'], entry['power_total'])
            new_entry['power_lower_ci'] = lower
            new_entry['power_upper_ci'] = upper
            
        results.append(new_entry)
    return results

def find_type_i_threshold(error_rates_with_ci: List[Dict[str, Any]], alpha: float = 0.05) -> Dict[str, Any]:
    """
    Identify the smallest sample size where Type I error lower CI bound > alpha.
    
    Args:
        error_rates_with_ci: List of error rate entries with CI bounds
        alpha: Significance level threshold (default 0.05)
        
    Returns:
        Dict with test_type, effect_size, threshold_n, and details
    """
    # Filter for Type I error conditions (effect_size == 0)
    type_i_data = [e for e in error_rates_with_ci if e.get('effect_size', 0) == 0]
    
    # Group by test_type
    by_test_type = {}
    for entry in type_i_data:
        t_type = entry['test_type']
        if t_type not in by_test_type:
            by_test_type[t_type] = []
        by_test_type[t_type].append(entry)
    
    thresholds = []
    for test_type, entries in by_test_type.items():
        # Sort by sample size
        sorted_entries = sorted(entries, key=lambda x: x['sample_size'])
        
        threshold_n = None
        for entry in sorted_entries:
            lower_ci = entry.get('type_i_lower_ci', 0)
            if lower_ci > alpha:
                threshold_n = entry['sample_size']
                break
        
        if threshold_n is not None:
            thresholds.append({
                'test_type': test_type,
                'effect_size': 0.0,
                'threshold_n': threshold_n,
                'metric': 'type_i_error_deviation',
                'alpha': alpha,
                'description': f"Smallest n where Type I error lower CI > {alpha}"
            })
    
    return thresholds

def find_power_threshold(error_rates_with_ci: List[Dict[str, Any]], power_target: float = 0.80, consecutive: int = 3) -> Dict[str, Any]:
    """
    Identify the smallest n where power CI remains >= power_target for 'consecutive' increments.
    
    Args:
        error_rates_with_ci: List of error rate entries with CI bounds
        power_target: Target power level (default 0.80)
        consecutive: Number of consecutive increments required
        
    Returns:
        Dict with test_type, effect_size, threshold_n, and details
    """
    # Filter for Power conditions (effect_size > 0)
    power_data = [e for e in error_rates_with_ci if e.get('effect_size', 0) > 0]
    
    # Group by (test_type, effect_size)
    groups = {}
    for entry in power_data:
        key = (entry['test_type'], entry['effect_size'])
        if key not in groups:
            groups[key] = []
        groups[key].append(entry)
    
    thresholds = []
    for (test_type, effect_size), entries in groups.items():
        sorted_entries = sorted(entries, key=lambda x: x['sample_size'])
        
        threshold_n = None
        consecutive_count = 0
        
        for entry in sorted_entries:
            lower_ci = entry.get('power_lower_ci', 0)
            if lower_ci >= power_target:
                consecutive_count += 1
                if consecutive_count >= consecutive:
                    threshold_n = entry['sample_size']
                    break
            else:
                consecutive_count = 0
        
        if threshold_n is not None:
            thresholds.append({
                'test_type': test_type,
                'effect_size': effect_size,
                'threshold_n': threshold_n,
                'metric': 'power_achieved',
                'power_target': power_target,
                'consecutive_required': consecutive,
                'description': f"Smallest n where power CI >= {power_target} for {consecutive} consecutive increments"
            })
    
    return thresholds

def save_thresholds(thresholds: List[Dict[str, Any]], output_path: str = "data/simulation/thresholds.json") -> None:
    """
    Save threshold metrics to a JSON file.
    
    Args:
        thresholds: List of threshold dictionaries
        output_path: Path to output JSON file
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    output_data = {
        "generated_at": str(np.datetime64('now')),
        "thresholds": thresholds
    }
    
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)

def load_error_rates(input_path: str = "data/simulation/error_rates_summary.csv") -> List[Dict[str, Any]]:
    """
    Load aggregated error rates from CSV.
    
    Args:
        input_path: Path to CSV file
        
    Returns:
        List of dictionaries representing rows
    """
    results = []
    if not os.path.exists(input_path):
        return results
        
    with open(input_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric strings to floats/ints
            cleaned_row = {}
            for k, v in row.items():
                if k in ['sample_size', 'type_i_count', 'type_i_total', 'power_count', 'power_total']:
                    cleaned_row[k] = int(v)
                elif k in ['effect_size', 'type_i_error_rate', 'power']:
                    cleaned_row[k] = float(v)
                else:
                    cleaned_row[k] = v
            results.append(cleaned_row)
    return results

def main():
    """
    Main entry point for threshold analysis.
    Reads error_rates_summary.csv, calculates thresholds, and saves to thresholds.json.
    """
    print("Loading error rates from data/simulation/error_rates_summary.csv...")
    error_rates = load_error_rates("data/simulation/error_rates_summary.csv")
    
    if not error_rates:
        print("No error rates found. Cannot calculate thresholds.")
        # Create empty thresholds file to satisfy artifact requirement
        save_thresholds([], "data/simulation/thresholds.json")
        return
        
    print(f"Loaded {len(error_rates)} error rate entries.")
    
    print("Calculating confidence intervals...")
    error_rates_with_ci = calculate_confidence_intervals(error_rates)
    
    print("Finding Type I error thresholds (alpha=0.05)...")
    type_i_thresholds = find_type_i_threshold(error_rates_with_ci, alpha=0.05)
    
    print("Finding power thresholds (target=0.80, consecutive=3)...")
    power_thresholds = find_power_threshold(error_rates_with_ci, power_target=0.80, consecutive=3)
    
    all_thresholds = type_i_thresholds + power_thresholds
    
    print(f"Found {len(all_thresholds)} thresholds.")
    for t in all_thresholds:
        print(f"  - {t['test_type']} (effect={t['effect_size']}): n={t['threshold_n']} ({t['metric']})")
    
    print("Saving thresholds to data/simulation/thresholds.json...")
    save_thresholds(all_thresholds, "data/simulation/thresholds.json")
    print("Done.")

if __name__ == "__main__":
    main()