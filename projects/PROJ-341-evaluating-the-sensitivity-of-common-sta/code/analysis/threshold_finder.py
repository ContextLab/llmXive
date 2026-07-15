import os
import json
import csv
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from scipy import stats

# Paths
ERROR_RATES_PATH = "data/simulation/error_rates_summary.csv"
THRESHOLDS_PATH = "data/simulation/thresholds.json"

def wilson_score_interval(
    successes: int,
    n: int,
    confidence: float = 0.95
) -> Tuple[float, float]:
    """
    Calculate Wilson score interval for a proportion.
    Returns (lower_bound, upper_bound).
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
    error_rates: List[Dict[str, Any]],
    confidence: float = 0.95
) -> List[Dict[str, Any]]:
    """
    Add Wilson score confidence intervals to error rate entries.
    """
    for entry in error_rates:
        n = entry.get('n_iterations', 10000)
        if entry['type'] == 'type_i':
            successes = entry.get('false_positives', 0)
        else:
            # For type II, we look at power (1 - type II error)
            # But we store type II error rate directly
            successes = entry.get('type_ii_errors', 0)
        
        lower, upper = wilson_score_interval(successes, n, confidence)
        
        entry['ci_lower'] = lower
        entry['ci_upper'] = upper
    
    return error_rates

def load_error_rates(csv_path: str = ERROR_RATES_PATH) -> List[Dict[str, Any]]:
    """Load error rates from CSV."""
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Error rates file not found: {csv_path}")
    
    rows = []
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric fields
            for key in ['sample_size', 'n_iterations', 'false_positives', 'type_ii_errors']:
                if key in row:
                    row[key] = int(row[key])
            for key in ['error_rate', 'power']:
                if key in row:
                    row[key] = float(row[key])
            rows.append(row)
    
    return rows

def find_type_i_threshold(
    error_rates: List[Dict[str, Any]],
    alpha: float = 0.05,
    min_ci_bound: float = 0.05
) -> Optional[int]:
    """
    Find the smallest sample size where Type I error lower CI bound > alpha.
    """
    for entry in sorted(error_rates, key=lambda x: x['sample_size']):
        if entry['type'] == 'type_i':
            ci_lower = entry.get('ci_lower', 0)
            if ci_lower > min_ci_bound:
                return entry['sample_size']
    return None

def find_power_threshold(
    error_rates: List[Dict[str, Any]],
    power_target: float = 0.80,
    consecutive_count: int = 3
) -> Optional[int]:
    """
    Find the smallest sample size where power CI remains >= target for consecutive increments.
    """
    sorted_data = sorted(error_rates, key=lambda x: x['sample_size'])
    consecutive_count_found = 0
    last_valid_n = None
    
    for entry in sorted_data:
        if entry['type'] == 'power':
            ci_lower = entry.get('ci_lower', 0)
            if ci_lower >= power_target:
                consecutive_count_found += 1
                if consecutive_count_found == 1:
                    last_valid_n = entry['sample_size']
                if consecutive_count_found >= consecutive_count:
                    return last_valid_n
            else:
                consecutive_count_found = 0
                last_valid_n = None
    
    return None

def save_thresholds(thresholds: Dict[str, Any], output_path: str = THRESHOLDS_PATH) -> str:
    """Save threshold metrics to JSON."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(thresholds, f, indent=2, default=str)
    
    return output_path

def main():
    """Main entry point: calculate and save thresholds."""
    print("Calculating reliability thresholds...")
    
    try:
        # Load error rates
        error_rates = load_error_rates()
        
        # Calculate confidence intervals
        error_rates = calculate_confidence_intervals(error_rates)
        
        # Group by test type and effect size
        thresholds = {
            "timestamp": str(np.datetime64('now')),
            "thresholds_by_test": {}
        }
        
        # Find thresholds for each test type
        test_types = set(e['test_type'] for e in error_rates)
        
        for test_type in test_types:
            test_data = [e for e in error_rates if e['test_type'] == test_type]
            thresholds["thresholds_by_test"][test_type] = {
                "type_i_threshold_n": find_type_i_threshold(test_data),
                "power_threshold_n": find_power_threshold(test_data)
            }
        
        # Save thresholds
        output_path = save_thresholds(thresholds)
        print(f"Thresholds saved to: {output_path}")
        
        # Print summary
        for test_type, t_data in thresholds["thresholds_by_test"].items():
            print(f"{test_type}: Type I threshold n={t_data['type_i_threshold_n']}, Power threshold n={t_data['power_threshold_n']}")
        
        return 0
    except Exception as e:
        print(f"Error calculating thresholds: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
