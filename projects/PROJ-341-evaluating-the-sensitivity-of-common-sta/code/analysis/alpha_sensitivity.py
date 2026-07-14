"""
Alpha Sensitivity Analysis Module (Task T035)

Implements sensitivity analysis for alpha thresholds across standard significance levels
to observe critical sample size shifts (SC-004).

This module:
1. Loads existing simulation results (error_rates_summary.csv)
2. Re-evaluates error rates for multiple alpha thresholds (0.01, 0.05, 0.10)
3. Identifies critical sample size shifts where test behavior changes significantly
4. Saves results to data/simulation/alpha_sensitivity_results.json
"""
import os
import json
import csv
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from code.analysis.aggregator import load_p_values_raw
from code.simulation.output_writer import load_p_values_raw as load_raw_pvalues
import warnings

# Standard alpha thresholds for sensitivity analysis
STANDARD_ALPHAS = [0.01, 0.05, 0.10]

def load_error_rates_from_csv(filepath: str) -> List[Dict[str, Any]]:
    """
    Load aggregated error rates from CSV file.
    
    Args:
        filepath: Path to error_rates_summary.csv
        
    Returns:
        List of dictionaries containing error rate data
    """
    results = []
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Error rates file not found: {filepath}")
    
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append({
                'sample_size': int(row['sample_size']),
                'test_type': row['test_type'],
                'effect_size': float(row['effect_size']),
                'hypothesis': row['hypothesis'],
                'type_i_error': float(row['type_i_error']),
                'type_ii_error': float(row['type_ii_error']),
                'power': float(row['power'])
            })
    return results

def recompute_error_rates_for_alpha(
    p_values: List[Dict[str, Any]], 
    alpha: float
) -> Dict[str, Any]:
    """
    Recompute error rates for a specific alpha threshold.
    
    Args:
        p_values: Raw p-values from simulation
        alpha: Significance threshold to evaluate
        
    Returns:
        Dictionary of recomputed error rates by condition
    """
    # Group by condition
    conditions = {}
    for record in p_values:
        key = (
            record['sample_size'],
            record['test_type'],
            record['effect_size'],
            record['hypothesis']
        )
        if key not in conditions:
            conditions[key] = []
        conditions[key].append(float(record['p_value']))
    
    # Calculate error rates for each condition
    error_rates = {}
    for key, p_vals in conditions.items():
        sample_size, test_type, effect_size, hypothesis = key
        p_vals = np.array(p_vals)
        
        if hypothesis == 'null':
            # Type I error: proportion of p < alpha when null is true
            type_i = np.mean(p_vals < alpha)
            type_ii = 0.0
            power = 0.0
        else:
            # Type II error: proportion of p >= alpha when alternative is true
            type_i = 0.0
            type_ii = np.mean(p_vals >= alpha)
            power = np.mean(p_vals < alpha)
        
        error_rates[key] = {
            'sample_size': sample_size,
            'test_type': test_type,
            'effect_size': effect_size,
            'hypothesis': hypothesis,
            'type_i_error': float(type_i),
            'type_ii_error': float(type_ii),
            'power': float(power)
        }
    
    return error_rates

def find_critical_sample_size_shifts(
    results_by_alpha: Dict[float, Dict[str, Any]],
    metric: str = 'power',
    threshold_change: float = 0.10
) -> List[Dict[str, Any]]:
    """
    Identify sample sizes where test behavior changes significantly across alpha thresholds.
    
    Args:
        results_by_alpha: Dictionary mapping alpha to error rate results
        metric: Metric to analyze ('power', 'type_i_error', 'type_ii_error')
        threshold_change: Minimum change in metric to consider significant
        
    Returns:
        List of critical shift points
    """
    shifts = []
    alphas = sorted(results_by_alpha.keys())
    
    # Get all unique conditions
    all_conditions = set()
    for alpha_data in results_by_alpha.values():
        all_conditions.update(alpha_data.keys())
    
    for condition in all_conditions:
        sample_size, test_type, effect_size, hypothesis = condition
        
        # Collect metric values across alphas
        metric_values = []
        for alpha in alphas:
            if condition in results_by_alpha[alpha]:
                val = results_by_alpha[alpha][condition].get(metric, 0.0)
                metric_values.append((alpha, val))
            else:
                metric_values.append((alpha, None))
        
        # Check for significant shifts
        for i in range(len(metric_values) - 1):
            alpha1, val1 = metric_values[i]
            alpha2, val2 = metric_values[i+1]
            
            if val1 is not None and val2 is not None:
                change = abs(val2 - val1)
                if change >= threshold_change:
                    shifts.append({
                        'condition': {
                            'sample_size': sample_size,
                            'test_type': test_type,
                            'effect_size': effect_size,
                            'hypothesis': hypothesis
                        },
                        'alpha_from': alpha1,
                        'alpha_to': alpha2,
                        'metric': metric,
                        'value_from': float(val1),
                        'value_to': float(val2),
                        'change': float(change)
                    })
    
    return shifts

def identify_threshold_shifts(
    results_by_alpha: Dict[float, Dict[str, Any]],
    target_power: float = 0.80,
    target_type_i: float = 0.05
) -> Dict[str, Any]:
    """
    Identify sample size thresholds that shift across alpha values.
    
    Args:
        results_by_alpha: Error rates organized by alpha
        target_power: Target power threshold
        target_type_i: Target Type I error threshold
        
    Returns:
        Dictionary of threshold shifts by test type and effect size
    """
    threshold_shifts = {}
    alphas = sorted(results_by_alpha.keys())
    
    # Group by test type and effect size
    test_effect_combos = set()
    for alpha_data in results_by_alpha.values():
        for key in alpha_data.keys():
            sample_size, test_type, effect_size, hypothesis = key
            test_effect_combos.add((test_type, effect_size, hypothesis))
    
    for test_type, effect_size, hypothesis in test_effect_combos:
        threshold_shifts[(test_type, effect_size, hypothesis)] = {}
        
        for alpha in alphas:
            # Find minimum sample size meeting criteria
            min_n = None
            for sample_size in sorted(set(k[0] for k in results_by_alpha[alpha].keys())):
                key = (sample_size, test_type, effect_size, hypothesis)
                if key in results_by_alpha[alpha]:
                    data = results_by_alpha[alpha][key]
                    
                    if hypothesis == 'null':
                        # Check Type I error
                        if data['type_i_error'] <= target_type_i + 0.02:  # Allow small tolerance
                            min_n = sample_size
                            break
                    else:
                        # Check power
                        if data['power'] >= target_power - 0.05:  # Allow small tolerance
                            min_n = sample_size
                            break
            
            if min_n is not None:
                threshold_shifts[(test_type, effect_size, hypothesis)][alpha] = min_n
    
    return threshold_shifts

def run_alpha_sensitivity_analysis(
    raw_pvalues_path: str = 'data/simulation/p_values_raw.csv',
    output_path: str = 'data/simulation/alpha_sensitivity_results.json'
) -> Dict[str, Any]:
    """
    Run complete alpha sensitivity analysis.
    
    Args:
        raw_pvalues_path: Path to raw p-values CSV
        output_path: Path for output JSON
        
    Returns:
        Dictionary containing analysis results
    """
    # Load raw p-values
    print(f"Loading raw p-values from {raw_pvalues_path}...")
    p_values = load_p_values_raw(raw_pvalues_path)
    
    if not p_values:
        raise ValueError("No p-values found in input file")
    
    # Recompute error rates for each alpha
    results_by_alpha = {}
    for alpha in STANDARD_ALPHAS:
        print(f"Computing error rates for alpha = {alpha}...")
        results_by_alpha[alpha] = recompute_error_rates_for_alpha(p_values, alpha)
    
    # Find critical shifts
    print("Identifying critical sample size shifts...")
    critical_shifts = find_critical_sample_size_shifts(results_by_alpha)
    
    # Identify threshold shifts
    print("Identifying threshold shifts...")
    threshold_shifts = identify_threshold_shifts(results_by_alpha)
    
    # Compile results
    results = {
        'analysis_metadata': {
            'alphas_analyzed': STANDARD_ALPHAS,
            'total_conditions': len(p_values),
            'timestamp': str(np.datetime64('now')),
            'source_file': raw_pvalues_path
        },
        'error_rates_by_alpha': {},
        'critical_shifts': critical_shifts,
        'threshold_shifts': {},
        'summary': {}
    }
    
    # Convert results_by_alpha to serializable format
    for alpha, data in results_by_alpha.items():
        results['error_rates_by_alpha'][str(alpha)] = list(data.values())
    
    # Convert threshold shifts to serializable format
    for key, shifts in threshold_shifts.items():
        test_type, effect_size, hypothesis = key
        results['threshold_shifts'][f"{test_type}_{effect_size}_{hypothesis}"] = {
            str(alpha): n for alpha, n in shifts.items()
        }
    
    # Generate summary statistics
    results['summary'] = {
        'total_critical_shifts': len(critical_shifts),
        'shifts_by_test_type': {},
        'shifts_by_alpha_pair': {}
    }
    
    for shift in critical_shifts:
        test_type = shift['condition']['test_type']
        alpha_pair = f"{shift['alpha_from']}_to_{shift['alpha_to']}"
        
        if test_type not in results['summary']['shifts_by_test_type']:
            results['summary']['shifts_by_test_type'][test_type] = 0
        results['summary']['shifts_by_test_type'][test_type] += 1
        
        if alpha_pair not in results['summary']['shifts_by_alpha_pair']:
            results['summary']['shifts_by_alpha_pair'][alpha_pair] = 0
        results['summary']['shifts_by_alpha_pair'][alpha_pair] += 1
    
    # Save results
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Alpha sensitivity analysis complete. Results saved to {output_path}")
    return results

def main():
    """Main entry point for alpha sensitivity analysis."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run alpha sensitivity analysis')
    parser.add_argument(
        '--input', 
        type=str, 
        default='data/simulation/p_values_raw.csv',
        help='Path to raw p-values CSV'
    )
    parser.add_argument(
        '--output', 
        type=str, 
        default='data/simulation/alpha_sensitivity_results.json',
        help='Path for output JSON'
    )
    
    args = parser.parse_args()
    
    try:
        results = run_alpha_sensitivity_analysis(args.input, args.output)
        print(f"Analysis completed successfully.")
        print(f"Found {len(results['critical_shifts'])} critical shifts across alpha thresholds.")
    except Exception as e:
        print(f"Error running alpha sensitivity analysis: {e}")
        raise

if __name__ == '__main__':
    main()