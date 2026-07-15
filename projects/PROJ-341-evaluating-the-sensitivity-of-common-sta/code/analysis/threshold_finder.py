import os
import json
import csv
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from scipy import stats

def wilson_score_interval(successes: int, trials: int, z: float = 1.96) -> Tuple[float, float]:
    """
    Calculate the Wilson score interval for a proportion.
    
    Args:
        successes: Number of successes (e.g., Type I errors observed)
        trials: Total number of trials (iterations)
        z: Z-score for confidence level (default 1.96 for 95%)
        
    Returns:
        Tuple of (lower_bound, upper_bound)
    """
    if trials == 0:
        return (0.0, 0.0)
        
    p_hat = successes / trials
    denominator = 1 + (z**2 / trials)
    centre = (p_hat + (z**2 / (2 * trials))) / denominator
    margin = (z / denominator) * np.sqrt((p_hat * (1 - p_hat) / trials) + (z**2 / (4 * trials**2)))
    
    return (centre - margin, centre + margin)

def calculate_confidence_intervals(error_rates: List[Dict[str, Any]], iterations: int = 10000) -> List[Dict[str, Any]]:
    """
    Calculate Wilson score confidence intervals for error rates.
    
    Args:
        error_rates: List of dictionaries containing 'type_i_count', 'type_ii_count', 
                     'sample_size', 'test_type', 'effect_size', etc.
        iterations: Total number of simulation iterations per condition
                    
    Returns:
        List of dictionaries with added CI bounds
    """
    results = []
    for row in error_rates:
        new_row = row.copy()
        
        # Type I error CI
        type_i_count = row.get('type_i_count', 0)
        lower_i, upper_i = wilson_score_interval(type_i_count, iterations)
        new_row['type_i_ci_lower'] = lower_i
        new_row['type_i_ci_upper'] = upper_i
        
        # Power (1 - Type II) CI
        # If we have type_ii_count, power = 1 - (type_ii / iterations)
        # But we need CI for power directly or derive from Type II CI
        type_ii_count = row.get('type_ii_count', 0)
        lower_ii, upper_ii = wilson_score_interval(type_ii_count, iterations)
        
        # Power = 1 - Type II rate
        # CI for power: [1 - upper_ii_rate, 1 - lower_ii_rate]
        power_lower = 1.0 - upper_ii
        power_upper = 1.0 - lower_ii
        
        new_row['power_ci_lower'] = max(0.0, power_lower)
        new_row['power_ci_upper'] = min(1.0, power_upper)
        new_row['type_ii_ci_lower'] = lower_ii
        new_row['type_ii_ci_upper'] = upper_ii
        
        results.append(new_row)
        
    return results

def load_error_rates(filepath: str = "data/simulation/error_rates_summary.csv") -> List[Dict[str, Any]]:
    """
    Load error rates from the aggregated CSV file.
    
    Args:
        filepath: Path to the error rates CSV
        
    Returns:
        List of dictionaries containing error rate data
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Error rates file not found: {filepath}")
        
    results = []
    with open(filepath, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric strings to appropriate types
            processed_row = {}
            for key, value in row.items():
                if key in ['sample_size', 'iterations', 'type_i_count', 'type_ii_count']:
                    processed_row[key] = int(value)
                elif key in ['effect_size', 'type_i_rate', 'type_ii_rate', 'power']:
                    processed_row[key] = float(value)
                else:
                    processed_row[key] = value
            results.append(processed_row)
            
    return results

def find_type_i_threshold(error_rates_with_ci: List[Dict[str, Any]], 
                          alpha: float = 0.05,
                          test_type: Optional[str] = None,
                          effect_size: Optional[float] = None) -> Optional[int]:
    """
    Find the smallest sample size where Type I error lower CI bound > alpha.
    
    Args:
        error_rates_with_ci: List of error rate data with confidence intervals
        alpha: Nominal significance level (default 0.05)
        test_type: Filter by specific test type (optional)
        effect_size: Filter by specific effect size (optional)
        
    Returns:
        Smallest sample size meeting the threshold, or None if not found
    """
    filtered = error_rates_with_ci
    if test_type:
        filtered = [r for r in filtered if r.get('test_type') == test_type]
    if effect_size is not None:
        filtered = [r for r in filtered if abs(float(r.get('effect_size', 0)) - effect_size) < 1e-6]
        
    # Sort by sample size
    filtered.sort(key=lambda x: x['sample_size'])
    
    for row in filtered:
        # Only consider Type I error cases (null hypothesis true)
        # Typically effect_size == 0 or very small for Type I error measurement
        if row.get('effect_size', 0) == 0:
            ci_lower = row.get('type_i_ci_lower', 0)
            if ci_lower > alpha:
                return row['sample_size']
                
    return None

def find_power_threshold(error_rates_with_ci: List[Dict[str, Any]],
                         target_power: float = 0.80,
                         test_type: Optional[str] = None,
                         effect_size: Optional[float] = None,
                         consecutive: int = 3) -> Optional[int]:
    """
    Find the smallest sample size where power CI remains >= target_power for 
    consecutive increments.
    
    Args:
        error_rates_with_ci: List of error rate data with confidence intervals
        target_power: Target power level (default 0.80)
        test_type: Filter by specific test type (optional)
        effect_size: Filter by specific effect size (optional)
        consecutive: Number of consecutive increments required (default 3)
        
    Returns:
        Smallest sample size meeting the threshold, or None if not found
    """
    filtered = error_rates_with_ci
    if test_type:
        filtered = [r for r in filtered if r.get('test_type') == test_type]
    if effect_size is not None:
        filtered = [r for r in filtered if abs(float(r.get('effect_size', 0)) - effect_size) < 1e-6]
        
    # Sort by sample size
    filtered.sort(key=lambda x: x['sample_size'])
    
    # Filter for alternative hypothesis cases (effect_size > 0)
    filtered = [r for r in filtered if r.get('effect_size', 0) > 0]
    
    if len(filtered) < consecutive:
        return None
        
    consecutive_count = 0
    for row in filtered:
        ci_lower = row.get('power_ci_lower', 0)
        if ci_lower >= target_power:
            consecutive_count += 1
            if consecutive_count >= consecutive:
                return row['sample_size']
        else:
            consecutive_count = 0
            
    return None

def save_thresholds(thresholds: Dict[str, Any], 
                    filepath: str = "data/simulation/thresholds.json") -> None:
    """
    Save threshold metrics to a JSON file.
    
    Args:
        thresholds: Dictionary containing threshold metrics
        filepath: Output path for the JSON file
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(thresholds, f, indent=2)

def main():
    """
    Main function to compute and save threshold metrics.
    Reads error_rates_summary.csv, calculates CIs, identifies thresholds,
    and saves results to thresholds.json.
    """
    error_rates_file = "data/simulation/error_rates_summary.csv"
    output_file = "data/simulation/thresholds.json"
    
    print(f"Loading error rates from {error_rates_file}...")
    try:
        error_rates = load_error_rates(error_rates_file)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please run the simulation first to generate error_rates_summary.csv")
        return
        
    print(f"Calculating confidence intervals for {len(error_rates)} conditions...")
    error_rates_with_ci = calculate_confidence_intervals(error_rates)
    
    # Identify thresholds for each test type and effect size combination
    thresholds = {
        "metadata": {
            "source_file": error_rates_file,
            "generated_at": str(__import__('datetime').datetime.now()),
            "alpha": 0.05,
            "target_power": 0.80
        },
        "thresholds": []
    }
    
    # Get unique combinations of test_type and effect_size
    unique_configs = set()
    for row in error_rates_with_ci:
        test_type = row.get('test_type', 'unknown')
        effect_size = row.get('effect_size', 0)
        unique_configs.add((test_type, effect_size))
        
    print(f"Identifying thresholds for {len(unique_configs)} configurations...")
    
    for test_type, effect_size in sorted(unique_configs):
        # Type I threshold (only for effect_size == 0)
        type_i_threshold = None
        if effect_size == 0:
            type_i_threshold = find_type_i_threshold(
                error_rates_with_ci, 
                alpha=0.05,
                test_type=test_type,
                effect_size=effect_size
            )
        
        # Power threshold (for effect_size > 0)
        power_threshold = None
        if effect_size > 0:
            power_threshold = find_power_threshold(
                error_rates_with_ci,
                target_power=0.80,
                test_type=test_type,
                effect_size=effect_size,
                consecutive=3
            )
        
        threshold_entry = {
            "test_type": test_type,
            "effect_size": effect_size,
            "type_i_threshold_n": type_i_threshold,
            "power_threshold_n": power_threshold
        }
        thresholds["thresholds"].append(threshold_entry)
        
    save_thresholds(thresholds, output_file)
    print(f"Threshold metrics saved to {output_file}")
    print(f"Summary:")
    for t in thresholds["thresholds"]:
        print(f"  {t['test_type']} (effect={t['effect_size']}): "
              f"Type I threshold n={t['type_i_threshold_n']}, "
              f"Power threshold n={t['power_threshold_n']}")

if __name__ == "__main__":
    main()