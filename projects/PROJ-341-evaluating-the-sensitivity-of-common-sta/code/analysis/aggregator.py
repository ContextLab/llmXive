import os
import csv
import json
from typing import List, Dict, Any, Optional
from code.simulation.output_writer import load_p_values_raw

def calculate_error_rates(p_values: List[Dict[str, Any]], alpha: float = 0.05) -> List[Dict[str, Any]]:
    """
    Calculate empirical Type I and Type II error rates from raw p-values.
    
    Type I Error: p < alpha when null hypothesis is true.
    Type II Error: p > alpha when alternative hypothesis is true (Power = 1 - Type II).
    
    Args:
        p_values: List of dictionaries containing simulation results.
        alpha: Significance threshold (default 0.05).
        
    Returns:
        List of dictionaries with aggregated error rates per condition.
    """
    if not p_values:
        return []

    # Group by condition (test_type, sample_size, effect_size, hypothesis)
    conditions = {}
    for row in p_values:
        key = (
            row.get('test_type'),
            row.get('sample_size'),
            row.get('effect_size'),
            row.get('hypothesis')
        )
        if key not in conditions:
            conditions[key] = []
        conditions[key].append(float(row.get('p_value', 1.0)))

    results = []
    for key, p_vals in conditions.items():
        test_type, sample_size, effect_size, hypothesis = key
        total = len(p_vals)
        if total == 0:
            continue

        # Count rejections
        rejections = sum(1 for p in p_vals if p < alpha)
        
        # Type I Error: Null is true (hypothesis='null') and we rejected (p < alpha)
        if hypothesis == 'null':
            type_i_count = rejections
            type_i_rate = type_i_count / total
            # Power is not applicable for null hypothesis
            power = None 
            type_ii_rate = None
        else:
            # Alternative is true
            # Type II Error: Fail to reject (p >= alpha)
            type_ii_count = total - rejections
            type_ii_rate = type_ii_count / total
            power = rejections / total
            type_i_rate = None

        results.append({
            'test_type': test_type,
            'sample_size': sample_size,
            'effect_size': effect_size,
            'hypothesis': hypothesis,
            'total_iterations': total,
            'alpha': alpha,
            'type_i_error_rate': type_i_rate,
            'type_ii_error_rate': type_ii_rate,
            'power': power,
            'rejection_count': rejections
        })

    return results

def save_aggregated_results(results: List[Dict[str, Any]], output_path: str) -> None:
    """
    Save aggregated error rates to a CSV file.
    
    Args:
        results: List of aggregated result dictionaries.
        output_path: Path to the output CSV file.
    """
    if not results:
        # Create empty file with headers if no data
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'test_type', 'sample_size', 'effect_size', 'hypothesis',
                'total_iterations', 'alpha', 'type_i_error_rate',
                'type_ii_error_rate', 'power', 'rejection_count'
            ])
            writer.writeheader()
        return

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Define fieldnames to ensure consistent column order
    fieldnames = [
        'test_type', 'sample_size', 'effect_size', 'hypothesis',
        'total_iterations', 'alpha', 'type_i_error_rate',
        'type_ii_error_rate', 'power', 'rejection_count'
    ]

    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            writer.writerow(row)

def main():
    """
    Main entry point for the aggregation task.
    Loads raw p-values, calculates error rates, and saves the summary.
    """
    input_path = 'data/simulation/p_values_raw.csv'
    output_path = 'data/simulation/error_rates_summary.csv'
    alpha = 0.05

    if not os.path.exists(input_path):
        print(f"Error: Input file not found: {input_path}")
        print("Please ensure T016 has been run to generate p_values_raw.csv.")
        return

    print(f"Loading raw p-values from {input_path}...")
    p_values = load_p_values_raw(input_path)
    print(f"Loaded {len(p_values)} raw p-value records.")

    print(f"Calculating error rates with alpha={alpha}...")
    results = calculate_error_rates(p_values, alpha)
    print(f"Calculated error rates for {len(results)} unique conditions.")

    print(f"Saving aggregated results to {output_path}...")
    save_aggregated_results(results, output_path)
    print(f"Successfully saved error rates summary to {output_path}.")

if __name__ == '__main__':
    main()