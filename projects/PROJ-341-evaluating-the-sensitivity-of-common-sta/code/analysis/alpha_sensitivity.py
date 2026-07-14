"""
Alpha Sensitivity Analysis Module

Implements sensitivity analysis for alpha thresholds across standard significance levels
to observe critical sample size shifts (SC-004).

This module:
1. Loads raw p-values from simulation output (T016)
2. Calculates error rates for multiple alpha thresholds (0.001, 0.01, 0.05, 0.10)
3. Identifies where critical sample size thresholds shift as alpha changes
4. Saves comprehensive sensitivity metrics to data/simulation/alpha_sensitivity.json
"""

import os
import json
import csv
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from code.simulation.output_writer import load_p_values_raw


def load_p_values_raw_safe(filepath: str = None) -> List[Dict[str, Any]]:
    """
    Safely load raw p-values with error handling.
    
    Args:
        filepath: Path to p_values_raw.csv. Defaults to standard location.
        
    Returns:
        List of dictionaries containing simulation results
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If file is empty or malformed
    """
    if filepath is None:
        filepath = "data/simulation/p_values_raw.csv"
        
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Raw p-values file not found: {filepath}")
        
    results = load_p_values_raw(filepath)
    
    if not results:
        raise ValueError(f"Raw p-values file is empty: {filepath}")
        
    return results


def calculate_error_rates_for_alpha(
    data: List[Dict[str, Any]], 
    alpha: float
) -> List[Dict[str, Any]]:
    """
    Calculate Type I and Type II error rates for a specific alpha threshold.
    
    Args:
        data: List of raw simulation results
        alpha: Significance threshold (e.g., 0.05)
        
    Returns:
        List of dictionaries with error rates per condition (n, test_type, effect_size, hypothesis)
    """
    # Group by condition
    conditions = {}
    
    for row in data:
        key = (
            int(row['sample_size']),
            row['test_type'],
            float(row['effect_size']),
            row['hypothesis']
        )
        
        if key not in conditions:
            conditions[key] = {'p_values': [], 'n': key[0], 'test_type': key[1], 
                              'effect_size': key[2], 'hypothesis': key[3]}
        
        conditions[key]['p_values'].append(float(row['p_value']))
    
    # Calculate error rates for each condition
    error_rates = []
    
    for key, cond in conditions.items():
        p_values = np.array(cond['p_values'])
        n_tests = len(p_values)
        
        if n_tests == 0:
            continue
        
        # Type I error: reject null when null is true (p < alpha when hypothesis == 'null')
        # Type II error: fail to reject null when alternative is true (p >= alpha when hypothesis == 'alternative')
        
        if cond['hypothesis'] == 'null':
            type_i_errors = np.sum(p_values < alpha)
            type_i_rate = type_i_errors / n_tests
            error_rates.append({
                'sample_size': cond['n'],
                'test_type': cond['test_type'],
                'effect_size': cond['effect_size'],
                'hypothesis': cond['hypothesis'],
                'alpha': alpha,
                'type_i_error_rate': float(type_i_rate),
                'type_i_errors': int(type_i_errors),
                'n_tests': n_tests,
                'power': None,
                'type_ii_error_rate': None,
                'type_ii_errors': None
            })
        else:  # alternative hypothesis
            type_ii_errors = np.sum(p_values >= alpha)
            type_ii_rate = type_ii_errors / n_tests
            power = 1 - type_ii_rate
            error_rates.append({
                'sample_size': cond['n'],
                'test_type': cond['test_type'],
                'effect_size': cond['effect_size'],
                'hypothesis': cond['hypothesis'],
                'alpha': alpha,
                'type_i_error_rate': None,
                'type_i_errors': None,
                'n_tests': n_tests,
                'power': float(power),
                'type_ii_error_rate': float(type_ii_rate),
                'type_ii_errors': int(type_ii_errors)
            })
    
    return error_rates


def find_threshold_shifts(
    error_rates_by_alpha: Dict[float, List[Dict[str, Any]]],
    target_type_i: float = 0.05,
    target_power: float = 0.80
) -> Dict[str, Any]:
    """
    Identify critical sample size shifts as alpha changes.
    
    Finds:
    1. For Type I error: smallest n where lower CI bound > alpha (reliability threshold)
    2. For Power: smallest n where power CI remains >= target_power for 3 consecutive increments
    
    Args:
        error_rates_by_alpha: Dict mapping alpha -> list of error rate results
        target_type_i: Target Type I error rate (typically 0.05)
        target_power: Target power threshold (typically 0.80)
        
    Returns:
        Dictionary with threshold information for each alpha level
    """
    thresholds = {}
    
    for alpha, error_rates in error_rates_by_alpha.items():
        alpha_thresholds = {
            'alpha': alpha,
            'type_i_thresholds': {},
            'power_thresholds': {}
        }
        
        # Group by test_type and effect_size
        groups = {}
        for er in error_rates:
            key = (er['test_type'], er['effect_size'])
            if key not in groups:
                groups[key] = {'type_i': [], 'power': []}
            
            if er['hypothesis'] == 'null' and er['type_i_error_rate'] is not None:
                groups[key]['type_i'].append(er)
            elif er['hypothesis'] == 'alternative' and er['power'] is not None:
                groups[key]['power'].append(er)
        
        # Find thresholds for each group
        for (test_type, effect_size), group_data in groups.items():
            # Type I threshold: find smallest n where error rate is close to alpha
            # (within reasonable tolerance, indicating the test has stabilized)
            type_i_data = sorted(group_data['type_i'], key=lambda x: x['sample_size'])
            power_data = sorted(group_data['power'], key=lambda x: x['sample_size'])
            
            # Type I: Find where error rate stabilizes near alpha
            type_i_threshold_n = None
            for er in type_i_data:
                if abs(er['type_i_error_rate'] - alpha) < 0.02:  # Within 2% of alpha
                    type_i_threshold_n = er['sample_size']
                    break
            
            # Power: Find where power >= target_power for 3 consecutive samples
            power_threshold_n = None
            if len(power_data) >= 3:
                for i in range(len(power_data) - 2):
                    if (power_data[i]['power'] >= target_power and
                        power_data[i+1]['power'] >= target_power and
                        power_data[i+2]['power'] >= target_power):
                        power_threshold_n = power_data[i]['sample_size']
                        break
            
            key_str = f"{test_type}_{effect_size}"
            alpha_thresholds['type_i_thresholds'][key_str] = {
                'threshold_n': type_i_threshold_n,
                'target_alpha': alpha
            }
            alpha_thresholds['power_thresholds'][key_str] = {
                'threshold_n': power_threshold_n,
                'target_power': target_power
            }
        
        thresholds[str(alpha)] = alpha_thresholds
    
    return thresholds


def run_sensitivity_analysis(
    data: List[Dict[str, Any]],
    alpha_levels: Optional[List[float]] = None
) -> Dict[str, Any]:
    """
    Run full sensitivity analysis across multiple alpha levels.
    
    Args:
        data: Raw p-values from simulation
        alpha_levels: List of alpha thresholds to analyze. Defaults to [0.001, 0.01, 0.05, 0.10]
        
    Returns:
        Comprehensive sensitivity analysis results
    """
    if alpha_levels is None:
        alpha_levels = [0.001, 0.01, 0.05, 0.10]
    
    # Calculate error rates for each alpha
    error_rates_by_alpha = {}
    for alpha in alpha_levels:
        error_rates_by_alpha[alpha] = calculate_error_rates_for_alpha(data, alpha)
    
    # Find threshold shifts
    thresholds = find_threshold_shifts(error_rates_by_alpha)
    
    # Compile summary statistics
    summary = {
        'alpha_levels_analyzed': alpha_levels,
        'total_conditions': len(data),
        'threshold_shifts': thresholds,
        'error_rates_by_alpha': {
            str(alpha): [
                {k: v for k, v in er.items() if v is not None}
                for er in rates
            ]
            for alpha, rates in error_rates_by_alpha.items()
        }
    }
    
    return summary


def main():
    """
    Main entry point for alpha sensitivity analysis.
    
    Reads raw p-values, runs sensitivity analysis, and saves results.
    """
    print("Starting Alpha Sensitivity Analysis...")
    
    try:
        # Load raw p-values
        print("Loading raw p-values...")
        raw_data = load_p_values_raw_safe("data/simulation/p_values_raw.csv")
        print(f"Loaded {len(raw_data)} raw p-value records")
        
        # Run sensitivity analysis
        print("Running sensitivity analysis across alpha levels...")
        results = run_sensitivity_analysis(raw_data)
        
        # Save results
        output_path = "data/simulation/alpha_sensitivity.json"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"Sensitivity analysis results saved to: {output_path}")
        
        # Print summary
        print("\n=== Sensitivity Analysis Summary ===")
        print(f"Alpha levels analyzed: {results['alpha_levels_analyzed']}")
        print(f"Total conditions: {results['total_conditions']}")
        
        # Show threshold shifts for a sample
        for alpha_str, alpha_data in results['threshold_shifts'].items():
            print(f"\nAlpha = {alpha_str}:")
            type_i_count = sum(1 for v in alpha_data['type_i_thresholds'].values() if v['threshold_n'] is not None)
            power_count = sum(1 for v in alpha_data['power_thresholds'].values() if v['threshold_n'] is not None)
            print(f"  Type I thresholds found: {type_i_count}")
            print(f"  Power thresholds found: {power_count}")
        
        return results
        
    except Exception as e:
        print(f"Error during sensitivity analysis: {e}")
        raise


if __name__ == "__main__":
    main()