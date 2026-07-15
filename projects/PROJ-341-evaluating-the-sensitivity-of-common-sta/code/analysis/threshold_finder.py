"""
Threshold identification and reliability analysis.

This module computes binomial confidence intervals (Wilson score) for error rates,
identifies sample size thresholds where error rates deviate from nominal alpha,
and saves threshold metrics to JSON.
"""
import os
import json
import csv
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from scipy import stats

# Import from local simulation module
from code.simulation.logging_config import get_logger

def wilson_score_interval(
    successes: int, 
    n: int, 
    confidence: float = 0.95
) -> Tuple[float, float]:
    """
    Calculate the Wilson score interval for a proportion.
    
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
    centre_adjusted_probability = p_hat + z**2 / (2 * n)
    adjusted_standard_deviation = np.sqrt(
        (p_hat * (1 - p_hat) / n) + (z**2 / (4 * n**2))
    )
    
    lower = (centre_adjusted_probability - z * adjusted_standard_deviation) / denominator
    upper = (centre_adjusted_probability + z * adjusted_standard_deviation) / denominator
    
    return max(0.0, lower), min(1.0, upper)

def calculate_confidence_intervals(
    error_rates_data: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Calculate Wilson score confidence intervals for all error rates.
    
    Args:
        error_rates_data: List of dicts with keys:
            - test_type: str
            - effect_size: float
            - sample_size: int
            - hypothesis: str ('null' or 'alternative')
            - type1_errors: int (count of Type I errors)
            - type2_errors: int (count of Type II errors, for power calculation)
            - iterations: int
            
    Returns:
        List of dicts with added CI bounds:
            - type1_ci_lower, type1_ci_upper
            - power_ci_lower, power_ci_upper (power = 1 - type2_error_rate)
    """
    results = []
    
    for row in error_rates_data:
        row_copy = row.copy()
        
        # Type I error CI (when hypothesis is null)
        if row['hypothesis'] == 'null':
            n = row['iterations']
            successes = row['type1_errors']
            lower, upper = wilson_score_interval(successes, n)
            row_copy['type1_ci_lower'] = lower
            row_copy['type1_ci_upper'] = upper
            
        # Power CI (when hypothesis is alternative)
        # Power = 1 - Type II error rate
        # Type II error count is stored as type2_errors
        elif row['hypothesis'] == 'alternative':
            n = row['iterations']
            # Power successes = iterations - type2_errors
            power_successes = n - row['type2_errors']
            lower, upper = wilson_score_interval(power_successes, n)
            row_copy['power_ci_lower'] = lower
            row_copy['power_ci_upper'] = upper
            
        results.append(row_copy)
        
    return results

def load_error_rates(filepath: str) -> List[Dict[str, Any]]:
    """
    Load error rates from CSV file.
    
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
            # Convert numeric fields
            processed_row = {
                'test_type': row['test_type'],
                'effect_size': float(row['effect_size']),
                'sample_size': int(row['sample_size']),
                'hypothesis': row['hypothesis'],
                'type1_errors': int(row['type1_errors']),
                'type2_errors': int(row['type2_errors']),
                'iterations': int(row['iterations']),
                'type1_error_rate': float(row['type1_error_rate']),
                'power': float(row['power'])
            }
            results.append(processed_row)
            
    return results

def find_type_i_threshold(
    error_rates_data: List[Dict[str, Any]],
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Find the smallest sample size where the Type I error lower CI bound exceeds alpha.
    
    This identifies when the test becomes unreliable (over-rejects null).
    
    Args:
        error_rates_data: List of error rate records with CI bounds
        alpha: Nominal significance level (default 0.05)
        
    Returns:
        Dict with:
            - test_type: str
            - effect_size: float (should be 0.0 for Type I)
            - threshold_n: int or None if never exceeded
            - ci_lower_at_threshold: float or None
            - alpha: float
    """
    logger = get_logger("threshold_finder")
    
    # Filter for null hypothesis and Type I error data
    null_data = [
        r for r in error_rates_data 
        if r['hypothesis'] == 'null' and 'type1_ci_lower' in r
    ]
    
    # Sort by sample size
    null_data.sort(key=lambda x: x['sample_size'])
    
    # Group by test_type and effect_size
    thresholds = {}
    
    for row in null_data:
        key = (row['test_type'], row['effect_size'])
        
        if key not in thresholds:
            # Check if lower CI exceeds alpha
            if row['type1_ci_lower'] > alpha:
                thresholds[key] = {
                    'test_type': row['test_type'],
                    'effect_size': row['effect_size'],
                    'threshold_n': row['sample_size'],
                    'ci_lower_at_threshold': row['type1_ci_lower'],
                    'alpha': alpha
                }
                logger.log("type_i_threshold_found", test_type=row['test_type'], 
                         effect_size=row['effect_size'], n=row['sample_size'])
    
    # Return list of thresholds
    return list(thresholds.values())

def find_power_threshold(
    error_rates_data: List[Dict[str, Any]],
    power_target: float = 0.80,
    consecutive_increments: int = 3
) -> List[Dict[str, Any]]:
    """
    Identify the smallest n where power CI remains below target for consecutive increments.
    
    This identifies when power is insufficient (underpowered tests).
    
    Args:
        error_rates_data: List of error rate records with CI bounds
        power_target: Target power level (default 0.80)
        consecutive_increments: Number of consecutive sample sizes to check (default 3)
        
    Returns:
        List of dicts with:
            - test_type: str
            - effect_size: float
            - threshold_n: int or None
            - power_ci_upper_at_threshold: float or None
    """
    logger = get_logger("threshold_finder")
    
    # Filter for alternative hypothesis (power data)
    alt_data = [
        r for r in error_rates_data 
        if r['hypothesis'] == 'alternative' and 'power_ci_upper' in r
    ]
    
    # Sort by sample size
    alt_data.sort(key=lambda x: x['sample_size'])
    
    # Group by test_type and effect_size
    thresholds = {}
    
    for key_group in set((r['test_type'], r['effect_size']) for r in alt_data):
        test_type, effect_size = key_group
        group = [r for r in alt_data if (r['test_type'], r['effect_size']) == key_group]
        
        # Check for consecutive increments below target
        consecutive_count = 0
        threshold_n = None
        power_upper = None
        
        for row in group:
            if row['power_ci_upper'] < power_target:
                consecutive_count += 1
                if consecutive_count >= consecutive_increments and threshold_n is None:
                    threshold_n = row['sample_size']
                    power_upper = row['power_ci_upper']
                    logger.log("power_threshold_found", test_type=test_type,
                             effect_size=effect_size, n=threshold_n)
                    break
            else:
                consecutive_count = 0
                
        if threshold_n is not None:
            thresholds[key_group] = {
                'test_type': test_type,
                'effect_size': effect_size,
                'threshold_n': threshold_n,
                'power_ci_upper_at_threshold': power_upper,
                'power_target': power_target
            }
    
    return list(thresholds.values())

def save_thresholds(
    type_i_thresholds: List[Dict[str, Any]],
    power_thresholds: List[Dict[str, Any]],
    output_path: str
) -> None:
    """
    Save threshold metrics to JSON file.
    
    Args:
        type_i_thresholds: List of Type I error threshold records
        power_thresholds: List of power threshold records
        output_path: Path to output JSON file
    """
    logger = get_logger("threshold_finder")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Combine thresholds into a single structure
    output_data = {
        'type_i_thresholds': type_i_thresholds,
        'power_thresholds': power_thresholds,
        'metadata': {
            'generated_at': datetime.utcnow().isoformat(),
            'description': 'Sample size thresholds for Type I error reliability and power adequacy'
        }
    }
    
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
        
    logger.log("thresholds_saved", output_path=output_path,
              type_i_count=len(type_i_thresholds), 
              power_count=len(power_thresholds))

def main():
    """Main entry point for threshold analysis."""
    logger = get_logger("threshold_finder")
    
    # Define paths
    error_rates_path = "data/simulation/error_rates_summary.csv"
    thresholds_output_path = "data/simulation/thresholds.json"
    
    logger.log("threshold_analysis_start", input_file=error_rates_path)
    
    # Load error rates
    error_rates_data = load_error_rates(error_rates_path)
    
    if not error_rates_data:
        logger.log("threshold_analysis_error", error="No error rate data found")
        # Create empty thresholds file
        save_thresholds([], [], thresholds_output_path)
        return
    
    # Calculate confidence intervals
    error_rates_with_ci = calculate_confidence_intervals(error_rates_data)
    
    # Find Type I thresholds
    type_i_thresholds = find_type_i_threshold(error_rates_with_ci, alpha=0.05)
    
    # Find power thresholds
    power_thresholds = find_power_threshold(
        error_rates_with_ci, 
        power_target=0.80, 
        consecutive_increments=3
    )
    
    # Save results
    save_thresholds(type_i_thresholds, power_thresholds, thresholds_output_path)
    
    logger.log("threshold_analysis_complete", output_file=thresholds_output_path)

if __name__ == "__main__":
    from datetime import datetime
    main()
