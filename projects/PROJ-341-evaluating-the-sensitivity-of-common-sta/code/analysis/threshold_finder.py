import os
import json
import csv
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from scipy import stats

def wilson_score_interval(count: int, n: int, z: float = 1.96) -> Tuple[float, float]:
    """
    Calculate the Wilson score interval for a proportion.
    count: number of successes (e.g., rejections)
    n: total trials
    z: z-score for confidence level (default 1.96 for 95%)
    """
    if n == 0:
        return 0.0, 0.0
    
    p_hat = count / n
    denominator = 1 + z**2 / n
    centre = (p_hat + z**2 / (2 * n)) / denominator
    margin = (z * np.sqrt((p_hat * (1 - p_hat) + z**2 / (4 * n)) / n)) / denominator
    
    lower = centre - margin
    upper = centre + margin
    
    return max(0.0, lower), min(1.0, upper)

def calculate_confidence_intervals(error_rates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Add Wilson score confidence intervals to error rate records.
    """
    results = []
    for row in error_rates:
        n = row['n']
        total_iterations = row.get('total_iterations', 10000) # Default fallback if not present
        # Ensure we use the actual count if available, otherwise calculate from rate
        if 'rejection_count' in row:
            count = row['rejection_count']
        else:
            rate = row['error_rate']
            count = int(rate * total_iterations)
        
        lower, upper = wilson_score_interval(count, total_iterations)
        
        result = row.copy()
        result['ci_lower'] = lower
        result['ci_upper'] = upper
        results.append(result)
    return results

def load_error_rates(filepath: str = 'data/simulation/error_rates_summary.csv') -> List[Dict[str, Any]]:
    """
    Load error rates from the aggregated CSV file.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Error rates file not found: {filepath}")
    
    data = []
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric strings to floats/ints
            for key in row:
                if key in ['n', 'total_iterations', 'rejection_count']:
                    try:
                        row[key] = int(row[key])
                    except ValueError:
                        row[key] = 0
                elif key in ['error_rate', 'ci_lower', 'ci_upper']:
                    try:
                        row[key] = float(row[key])
                    except ValueError:
                        row[key] = 0.0
            data.append(row)
    return data

def find_type_i_threshold(data: List[Dict[str, Any]], alpha: float = 0.05) -> Optional[int]:
    """
    Identify the smallest n where Type I error lower CI bound > alpha.
    Filters for Null=True (Type I error context).
    """
    # Filter for Null hypothesis (Type I error)
    type_i_data = [r for r in data if r.get('hypothesis', '').lower() == 'null']
    if not type_i_data:
        return None
    
    # Sort by sample size
    type_i_data.sort(key=lambda x: x['n'])
    
    for row in type_i_data:
        if row.get('ci_lower') is not None and row['ci_lower'] > alpha:
            return row['n']
    return None

def find_power_threshold(data: List[Dict[str, Any]], power_target: float = 0.80) -> Optional[int]:
    """
    Identify the smallest n where power CI remains >= power_target for 3 consecutive increments.
    Filters for Alt=True (Power context).
    """
    # Filter for Alternative hypothesis (Power context)
    power_data = [r for r in data if r.get('hypothesis', '').lower() == 'alt']
    if not power_data:
        return None
    
    # Sort by sample size
    power_data.sort(key=lambda x: x['n'])
    
    consecutive_count = 0
    last_valid_n = None
    
    for row in power_data:
        ci_lower = row.get('ci_lower')
        if ci_lower is not None and ci_lower >= power_target:
            consecutive_count += 1
            last_valid_n = row['n']
            if consecutive_count >= 3:
                return last_valid_n
        else:
            consecutive_count = 0
            last_valid_n = None
    
    return None

def save_thresholds(thresholds: Dict[str, Any], filepath: str = 'data/simulation/thresholds.json'):
    """
    Save threshold metrics to JSON.
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(thresholds, f, indent=2)

def main():
    """
    Main entry point for T023: Save threshold metrics to data/simulation/thresholds.json.
    Reads from data/simulation/error_rates_summary.csv (produced by T018).
    """
    input_file = 'data/simulation/error_rates_summary.csv'
    output_file = 'data/simulation/thresholds.json'
    
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file not found: {input_file}. Run T018 first.")
    
    print(f"Loading error rates from {input_file}...")
    error_rates = load_error_rates(input_file)
    
    if not error_rates:
        raise ValueError("No error rate data found in input file.")
    
    # Group by test_type and effect_size to find thresholds per condition
    unique_conditions = set()
    for row in error_rates:
        key = (row['test_type'], row.get('effect_size', 0.0))
        unique_conditions.add(key)
    
    thresholds = {
        "metadata": {
            "source_file": input_file,
            "alpha": 0.05,
            "power_target": 0.80,
            "consecutive_samples_required": 3
        },
        "results": []
    }
    
    for test_type, effect_size in unique_conditions:
        # Filter data for this condition
        condition_data = [
            r for r in error_rates 
            if r['test_type'] == test_type and float(r.get('effect_size', 0.0)) == float(effect_size)
        ]
        
        # Calculate CI if not present
        condition_data = calculate_confidence_intervals(condition_data)
        
        # Find Type I threshold (only relevant if effect_size is 0 or null hypothesis context)
        # We look at the 'hypothesis' column in the data. If the row is 'null', it's Type I.
        # If the row is 'alt', it's Power.
        
        # For Type I threshold, we specifically need the 'null' hypothesis rows for this test type
        # Even if effect_size is non-zero, Type I error is defined under Null. 
        # However, in our simulation grid, 'null' hypothesis usually implies effect_size=0.
        # Let's find the threshold for the 'null' hypothesis rows specifically.
        type_i_threshold = find_type_i_threshold(condition_data)
        
        # For Power threshold, we need 'alt' hypothesis rows
        power_threshold = find_power_threshold(condition_data)
        
        thresholds["results"].append({
            "test_type": test_type,
            "effect_size": effect_size,
            "type_i_threshold_n": type_i_threshold,
            "power_threshold_n": power_threshold
        })
    
    save_thresholds(thresholds, output_file)
    print(f"Thresholds saved to {output_file}")
    print(f"Found {len(thresholds['results'])} unique conditions.")
    for res in thresholds['results']:
        print(f"  {res['test_type']} (effect={res['effect_size']}): TypeI_N={res['type_i_threshold_n']}, Power_N={res['power_threshold_n']}")

if __name__ == "__main__":
    main()