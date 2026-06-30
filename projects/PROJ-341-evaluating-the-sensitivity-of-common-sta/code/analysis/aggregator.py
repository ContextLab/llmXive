import os
import csv
import json
from typing import List, Dict, Any, Optional
from code.simulation.output_writer import load_p_values_raw

def calculate_error_rates(p_values_data: List[Dict[str, Any]], alpha: float = 0.05) -> List[Dict[str, Any]]:
    """
    Calculate empirical Type I and Type II error rates from raw p-values.

    Args:
        p_values_data: List of dicts containing simulation results with keys:
            - sample_size (int)
            - effect_size (float)
            - test_type (str)
            - p_value (float)
            - hypothesis (str): 'null' or 'alternative'
        alpha: Significance threshold (default 0.05)

    Returns:
        List of aggregated error rate dictionaries per condition.
    """
    if not p_values_data:
        return []

    # Group by condition
    conditions = {}
    for row in p_values_data:
        key = (row['sample_size'], row['effect_size'], row['test_type'], row['hypothesis'])
        if key not in conditions:
            conditions[key] = {'p_values': [], 'hypothesis': row['hypothesis']}
        conditions[key]['p_values'].append(row['p_value'])

    results = []
    for key, data in conditions.items():
        sample_size, effect_size, test_type, hypothesis_type = key
        p_vals = data['p_values']
        total_count = len(p_vals)

        if total_count == 0:
            continue

        # Calculate error rates
        if hypothesis_type == 'null':
            # Type I error: rejecting null when it is true (p < alpha)
            rejections = sum(1 for p in p_vals if p < alpha)
            error_rate = rejections / total_count
            error_type = 'Type_I'
        else:
            # Type II error: failing to reject null when alternative is true (p >= alpha)
            # Power = 1 - Type II error
            non_rejections = sum(1 for p in p_vals if p >= alpha)
            type_ii_rate = non_rejections / total_count
            power = 1.0 - type_ii_rate
            error_rate = type_ii_rate
            error_type = 'Type_II'

        results.append({
            'sample_size': sample_size,
            'effect_size': effect_size,
            'test_type': test_type,
            'hypothesis': hypothesis_type,
            'total_iterations': total_count,
            'error_rate': error_rate,
            'error_type': error_type,
            'alpha': alpha
        })

    return results

def save_aggregated_results(results: List[Dict[str, Any]], output_path: str) -> None:
    """
    Save aggregated error rates to a CSV file.

    Args:
        results: List of aggregated error rate dictionaries.
        output_path: Path to the output CSV file.
    """
    if not results:
        raise ValueError("No results to save.")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    fieldnames = [
        'sample_size', 'effect_size', 'test_type', 'hypothesis',
        'total_iterations', 'error_rate', 'error_type', 'alpha'
    ]

    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

def main():
    """
    Main entry point for T018: Load raw p-values, calculate error rates, and save summary.
    """
    input_path = 'data/simulation/p_values_raw.csv'
    output_path = 'data/simulation/error_rates_summary.csv'

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    print(f"Loading raw p-values from {input_path}...")
    p_values_data = load_p_values_raw(input_path)
    print(f"Loaded {len(p_values_data)} raw p-value records.")

    print("Calculating error rates...")
    aggregated_results = calculate_error_rates(p_values_data)
    print(f"Calculated error rates for {len(aggregated_results)} conditions.")

    print(f"Saving aggregated results to {output_path}...")
    save_aggregated_results(aggregated_results, output_path)
    print("Done.")

if __name__ == "__main__":
    main()