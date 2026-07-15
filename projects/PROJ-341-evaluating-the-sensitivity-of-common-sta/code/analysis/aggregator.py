"""
Aggregator for simulation results.
Implements T017: Calculate empirical Type I and Type II error rates.
"""
import os
import csv
import json
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np

from code.simulation.logging_config import get_logger, log_operation
from code.simulation.output_writer import load_p_values_raw

def calculate_error_rates(raw_data: List[Dict[str, Any]], alpha: float = 0.05) -> List[Dict[str, Any]]:
    """
    Calculate empirical Type I and Type II error rates from raw p-values.
    
    Type I Error: Rejecting null when null is true (p < alpha when hypothesis == 'null')
    Type II Error: Failing to reject null when alternative is true (p > alpha when hypothesis == 'alternative')
    
    Args:
        raw_data: List of dicts with keys: sample_size, effect_size, test_type, p_value, hypothesis
        alpha: Significance threshold (default 0.05)
        
    Returns:
        List of aggregated error rate records per condition.
    """
    if not raw_data:
        return []
    
    df = pd.DataFrame(raw_data)
    
    # Ensure numeric columns
    df['p_value'] = pd.to_numeric(df['p_value'], errors='coerce')
    df['sample_size'] = pd.to_numeric(df['sample_size'], errors='coerce')
    df['effect_size'] = pd.to_numeric(df['effect_size'], errors='coerce')
    
    # Filter out rows with invalid p-values
    valid_df = df.dropna(subset=['p_value'])
    
    if valid_df.empty:
        return []
    
    # Group by condition
    grouped = valid_df.groupby(['sample_size', 'effect_size', 'test_type', 'hypothesis'])
    
    results = []
    
    for (sample_size, effect_size, test_type, hypothesis), group in grouped:
        total_count = len(group)
        if total_count == 0:
            continue
            
        # Calculate errors based on hypothesis type
        if hypothesis == 'null':
            # Type I error: p < alpha when null is true
            error_count = (group['p_value'] < alpha).sum()
            error_type = 'type_i'
        else:  # hypothesis == 'alternative'
            # Type II error: p > alpha when alternative is true
            error_count = (group['p_value'] > alpha).sum()
            error_type = 'type_ii'
        
        error_rate = error_count / total_count
        
        results.append({
            'sample_size': int(sample_size),
            'effect_size': float(effect_size),
            'test_type': test_type,
            'hypothesis': hypothesis,
            'error_type': error_type,
            'total_iterations': total_count,
            'error_count': int(error_count),
            'error_rate': float(error_rate),
            'alpha_threshold': alpha
        })
    
    return results

def save_aggregated_results(error_rates: List[Dict[str, Any]], output_path: str) -> None:
    """
    Save aggregated error rates to a CSV file.
    
    Args:
        error_rates: List of error rate dictionaries
        output_path: Path to the output CSV file
    """
    if not error_rates:
        # Write empty file with headers if no data
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', newline='') as f:
            fieldnames = ['sample_size', 'effect_size', 'test_type', 'hypothesis', 
                         'error_type', 'total_iterations', 'error_count', 'error_rate', 'alpha_threshold']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
        return
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', newline='') as f:
        fieldnames = ['sample_size', 'effect_size', 'test_type', 'hypothesis', 
                     'error_type', 'total_iterations', 'error_count', 'error_rate', 'alpha_threshold']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(error_rates)

def main() -> None:
    """
    Main entry point for the aggregation task.
    Loads raw p-values, calculates error rates, and saves the summary.
    """
    input_path = 'data/simulation/p_values_raw.csv'
    output_path = 'data/simulation/error_rates_summary.csv'
    alpha = 0.05
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}. "
                              "Run the simulation first to generate p_values_raw.csv")
    
    # Load raw data
    raw_data = load_p_values_raw(input_path)
    
    if not raw_data:
        print("Warning: No raw data found. Creating empty summary file.")
        save_aggregated_results([], output_path)
        return
    
    # Calculate error rates
    error_rates = calculate_error_rates(raw_data, alpha)
    
    # Save results
    save_aggregated_results(error_rates, output_path)
    
    print(f"Aggregated {len(error_rates)} error rate records to {output_path}")

if __name__ == '__main__':
    main()
