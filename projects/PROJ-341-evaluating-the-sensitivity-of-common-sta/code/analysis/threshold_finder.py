import os
import json
import csv
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from scipy import stats


def wilson_score_interval(successes: float, n: float, confidence: float = 0.95) -> Tuple[float, float]:
    """
    Calculate the Wilson score interval for a proportion.
    
    Args:
        successes: Number of successes (e.g., Type I errors observed)
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
    margin = (z * np.sqrt(p_hat * (1 - p_hat) / n + z**2 / (4 * n**2))) / denominator
    
    return center - margin, center + margin


def calculate_confidence_intervals(error_rates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Calculate Wilson score confidence intervals for all error rates.
    
    Args:
        error_rates: List of dictionaries containing error rate data
                    
    Returns:
        List of dictionaries with added CI bounds
    """
    result = []
    for row in error_rates:
        n = row['n']
        successes = row['successes']
        alpha = row.get('alpha', 0.05)
        test_type = row['test_type']
        effect_size = row['effect_size']
        hypothesis = row['hypothesis']
        
        lower, upper = wilson_score_interval(successes, n)
        
        row_with_ci = row.copy()
        row_with_ci['ci_lower'] = lower
        row_with_ci['ci_upper'] = upper
        result.append(row_with_ci)
        
    return result


def find_type_i_threshold(error_rates: List[Dict[str, Any]], alpha: float = 0.05) -> Optional[int]:
    """
    Identify the smallest n where Type I error lower CI bound > alpha.
    
    Args:
        error_rates: List of error rate dictionaries (must include Type I data)
        alpha: Significance level threshold
        
    Returns:
        The smallest sample size n meeting the criterion, or None if not found
    """
    type_i_rows = [r for r in error_rates if r['hypothesis'] == 'H0' and r['test_type'] != 'ANOVA']
    # Sort by n
    type_i_rows.sort(key=lambda x: x['n'])
    
    for row in type_i_rows:
        if row['ci_lower'] > alpha:
            return row['n']
            
    return None


def find_power_threshold(error_rates: List[Dict[str, Any]], power_target: float = 0.80, consecutive_count: int = 3) -> Optional[int]:
    """
    Identify the smallest n where power CI remains < power_target for consecutive_count increments.
    
    Args:
        error_rates: List of error rate dictionaries (must include Type II/Power data)
        power_target: Target power level (default 0.80)
        consecutive_count: Number of consecutive increments required
        
    Returns:
        The smallest sample size n meeting the criterion, or None if not found
    """
    # Filter for Type II (H1) data, excluding ANOVA for simplicity in this check
    type_ii_rows = [r for r in error_rates if r['hypothesis'] == 'H1' and r['test_type'] != 'ANOVA']
    type_ii_rows.sort(key=lambda x: x['n'])
    
    if len(type_ii_rows) < consecutive_count:
        return None
        
    # Power = 1 - Type II error rate. 
    # We look for where the LOWER bound of power CI is < target.
    # Power CI Lower = 1 - Upper CI of Type II error.
    
    consecutive_failures = 0
    last_valid_n = None
    
    for i in range(len(type_ii_rows) - consecutive_count + 1):
        window = type_ii_rows[i:i+consecutive_count]
        all_below = True
        
        for row in window:
            # Calculate power lower bound: 1 - row['ci_upper'] (since ci_upper is for Type II error)
            power_lower = 1.0 - row['ci_upper']
            if power_lower >= power_target:
                all_below = False
                break
        
        if all_below:
            # Found a window where power is consistently below target
            # The threshold is the n of the first element in this window
            return window[0]['n']
            
    return None


def save_thresholds(thresholds: Dict[str, Any], output_path: str) -> None:
    """
    Save threshold metrics to a JSON file.
    
    Args:
        thresholds: Dictionary containing threshold results
        output_path: Path to the output JSON file
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(thresholds, f, indent=2)


def main() -> None:
    """
    Main entry point for threshold analysis.
    Reads aggregated error rates, calculates CIs, finds thresholds, and saves results.
    """
    input_path = 'data/simulation/error_rates_summary.csv'
    output_path = 'data/simulation/thresholds.json'
    
    if not os.path.exists(input_path):
        print(f"Error: Input file {input_path} not found.")
        return

    # Load data
    error_rates = []
    with open(input_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert string numbers to float/int
            row['n'] = int(row['n'])
            row['successes'] = int(row['successes'])
            row['total'] = int(row['total'])
            row['alpha'] = float(row['alpha'])
            row['effect_size'] = float(row['effect_size'])
            error_rates.append(row)
    
    # Calculate confidence intervals
    error_rates_with_ci = calculate_confidence_intervals(error_rates)
    
    # Group by test_type and effect_size to find thresholds per condition
    conditions = {}
    for row in error_rates_with_ci:
        key = (row['test_type'], row['effect_size'])
        if key not in conditions:
            conditions[key] = []
        conditions[key].append(row)
    
    thresholds = {
        "metadata": {
            "source_file": input_path,
            "generated_at": str(__import__('datetime').datetime.now()),
            "description": "Thresholds for Type I error inflation and Power deficiency"
        },
        "results": []
    }
    
    for (test_type, effect_size), rows in conditions.items():
        type_i_n = find_type_i_threshold(rows)
        power_n = find_power_threshold(rows)
        
        threshold_entry = {
            "test_type": test_type,
            "effect_size": effect_size,
            "type_i_threshold_n": type_i_n,
            "power_threshold_n": power_n,
            "notes": []
        }
        
        if type_i_n is None:
            threshold_entry["notes"].append("No Type I inflation threshold found (CI never > alpha)")
        if power_n is None:
            threshold_entry["notes"].append("No power deficiency threshold found (Power >= 0.80 early or insufficient data)")
            
        thresholds["results"].append(threshold_entry)
    
    save_thresholds(thresholds, output_path)
    print(f"Thresholds saved to {output_path}")


if __name__ == "__main__":
    main()