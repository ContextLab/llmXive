import os
import csv
import json
from typing import List, Dict, Any, Optional
import pandas as pd
from code.simulation.output_writer import load_p_values_raw

def calculate_error_rates(p_values: List[Dict[str, Any]], alpha: float = 0.05) -> List[Dict[str, Any]]:
    """
    Calculate empirical Type I and Type II error rates from raw p-values.
    
    Args:
        p_values: List of dicts containing simulation results with keys:
                  'sample_size', 'effect_size', 'test_type', 'p_value', 'hypothesis'
        alpha: Significance threshold (default 0.05)
    
    Returns:
        List of aggregated error rate records.
    """
    if not p_values:
        return []
    
    df = pd.DataFrame(p_values)
    
    # Ensure hypothesis column is boolean or string
    df['is_null_true'] = df['hypothesis'].apply(lambda x: x == 'null' or x is True)
    df['is_rejected'] = df['p_value'] < alpha
    
    results = []
    
    # Group by sample_size, effect_size, test_type
    grouped = df.groupby(['sample_size', 'effect_size', 'test_type'])
    
    for (sample_size, effect_size, test_type), group in grouped:
        # Type I Error: Rejecting Null when Null is True
        null_group = group[group['is_null_true']]
        if len(null_group) > 0:
            type_i_errors = null_group['is_rejected'].sum()
            type_i_rate = type_i_errors / len(null_group)
            results.append({
                'sample_size': sample_size,
                'effect_size': effect_size,
                'test_type': test_type,
                'hypothesis': 'null',
                'total_iterations': len(null_group),
                'type_i_errors': type_i_errors,
                'type_i_rate': type_i_rate,
                'alpha': alpha
            })
        
        # Type II Error: Failing to reject Null when Alternative is True
        alt_group = group[~group['is_null_true']]
        if len(alt_group) > 0:
            type_2_errors = (~alt_group['is_rejected']).sum()
            type_2_rate = type_2_errors / len(alt_group)
            # Power = 1 - Type II Error Rate
            power = 1 - type_2_rate
            results.append({
                'sample_size': sample_size,
                'effect_size': effect_size,
                'test_type': test_type,
                'hypothesis': 'alternative',
                'total_iterations': len(alt_group),
                'type_2_errors': type_2_errors,
                'type_2_rate': type_2_rate,
                'power': power,
                'alpha': alpha
            })
    
    return results

def save_aggregated_results(error_rates: List[Dict[str, Any]], output_path: str) -> None:
    """
    Save aggregated error rates to a CSV file.
    
    Args:
        error_rates: List of error rate dictionaries.
        output_path: Path to the output CSV file.
    """
    if not error_rates:
        print("Warning: No error rates to save.")
        # Create empty file with headers
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        pd.DataFrame().to_csv(output_path, index=False)
        return
    
    df = pd.DataFrame(error_rates)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Saved aggregated error rates to {output_path} ({len(error_rates)} rows)")

def main():
    """
    Main entry point for the aggregator.
    Loads raw p-values, calculates error rates, and saves the summary.
    """
    raw_pvalues_path = "data/simulation/p_values_raw.csv"
    output_path = "data/simulation/error_rates_summary.csv"
    
    if not os.path.exists(raw_pvalues_path):
        raise FileNotFoundError(
            f"Input file not found: {raw_pvalues_path}. "
            "Please run the simulation first to generate p_values_raw.csv."
        )
    
    print(f"Loading raw p-values from {raw_pvalues_path}...")
    p_values = load_p_values_raw(raw_pvalues_path)
    print(f"Loaded {len(p_values)} raw p-value records.")
    
    print("Calculating error rates...")
    error_rates = calculate_error_rates(p_values)
    
    print(f"Saving aggregated results to {output_path}...")
    save_aggregated_results(error_rates, output_path)
    
    print("Aggregation complete.")

if __name__ == "__main__":
    main()