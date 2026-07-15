import os
import csv
import json
from typing import List, Dict, Any, Optional
from code.simulation.output_writer import load_p_values_raw

def calculate_error_rates(p_values: List[Dict[str, Any]], alpha: float = 0.05) -> List[Dict[str, Any]]:
    """
    Calculate empirical Type I and Type II error rates from raw p-values.
    
    Type I Error: Rejecting null when it is true (p < alpha when hypothesis_state == 'null')
    Type II Error: Failing to reject null when it is false (p > alpha when hypothesis_state == 'alternative')
    Power: 1 - Type II Error (p < alpha when hypothesis_state == 'alternative')
    
    Args:
        p_values: List of dicts with keys: sample_size, effect_size, test_type, p_value, hypothesis_state
        alpha: Significance threshold (default 0.05)
        
    Returns:
        List of aggregated error rate dictionaries
    """
    if not p_values:
        return []
    
    # Group by condition
    conditions = {}
    for row in p_values:
        key = (row['sample_size'], row['effect_size'], row['test_type'], row['hypothesis_state'])
        if key not in conditions:
            conditions[key] = {'p_values': [], 'hypothesis_state': row['hypothesis_state']}
        conditions[key]['p_values'].append(float(row['p_value']))
    
    results = []
    for (n, effect_size, test_type, hyp_state), data in conditions.items():
        p_vals = data['p_values']
        total_count = len(p_vals)
        
        if hyp_state == 'null':
            # Type I error rate
            rejections = sum(1 for p in p_vals if p < alpha)
            error_rate = rejections / total_count if total_count > 0 else 0.0
            metric_type = 'type_i_error'
        else:
            # Type II error rate and Power
            non_rejections = sum(1 for p in p_vals if p > alpha)
            type_ii_rate = non_rejections / total_count if total_count > 0 else 0.0
            power = 1.0 - type_ii_rate
            results.append({
                'sample_size': n,
                'effect_size': effect_size,
                'test_type': test_type,
                'hypothesis_state': hyp_state,
                'metric_type': 'type_ii_error',
                'error_rate': type_ii_rate,
                'total_iterations': total_count,
                'rejections': total_count - non_rejections,
                'non_rejections': non_rejections
            })
            results.append({
                'sample_size': n,
                'effect_size': effect_size,
                'test_type': test_type,
                'hypothesis_state': hyp_state,
                'metric_type': 'power',
                'error_rate': power, # Power is technically not an error rate, but stored in same column for consistency
                'total_iterations': total_count,
                'rejections': total_count - non_rejections,
                'non_rejections': non_rejections
            })
            continue
        
        results.append({
            'sample_size': n,
            'effect_size': effect_size,
            'test_type': test_type,
            'hypothesis_state': hyp_state,
            'metric_type': metric_type,
            'error_rate': error_rate,
            'total_iterations': total_count,
            'rejections': rejections,
            'non_rejections': total_count - rejections
        })
    
    return results

def save_aggregated_results(results: List[Dict[str, Any]], output_path: str) -> None:
    """
    Save aggregated error rates to a CSV file.
    
    Args:
        results: List of aggregated result dictionaries
        output_path: Path to the output CSV file
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    fieldnames = [
        'sample_size', 'effect_size', 'test_type', 'hypothesis_state', 
        'metric_type', 'error_rate', 'total_iterations', 'rejections', 'non_rejections'
    ]
    
    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

def main():
    """Main entry point for the aggregator script."""
    input_path = 'data/simulation/p_values_raw.csv'
    output_path = 'data/simulation/error_rates_summary.csv'
    alpha = 0.05
    
    if not os.path.exists(input_path):
        print(f"Error: Input file not found: {input_path}")
        print("Please run the simulation first to generate p_values_raw.csv")
        return 1
    
    print(f"Loading raw p-values from {input_path}...")
    p_values = load_p_values_raw(input_path)
    
    if not p_values:
        print("Error: No p-values found in the input file.")
        return 1
    
    print(f"Calculating error rates for {len(p_values)} records with alpha={alpha}...")
    results = calculate_error_rates(p_values, alpha)
    
    print(f"Saving aggregated results to {output_path}...")
    save_aggregated_results(results, output_path)
    
    print(f"Success! Aggregated {len(results)} error rate metrics.")
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main())