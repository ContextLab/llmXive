import os
import csv
import json
from typing import List, Dict, Any, Optional
import pandas as pd
from code.simulation.output_writer import load_p_values_raw

def calculate_error_rates(p_values_df: pd.DataFrame, alpha: float = 0.05) -> pd.DataFrame:
    """
    Calculate empirical Type I and Type II error rates from raw p-values.
    
    Type I Error: Reject H0 when H0 is true (p < alpha AND hypothesis == 'H0')
    Type II Error: Fail to reject H0 when H1 is true (p > alpha AND hypothesis == 'H1')
    
    Args:
        p_values_df: DataFrame with columns: sample_size, effect_size, test_type, p_value, hypothesis
        alpha: Significance threshold (default 0.05)
        
    Returns:
        DataFrame with aggregated error rates per condition
    """
    if p_values_df.empty:
        return pd.DataFrame()
    
    # Ensure numeric types
    p_values_df = p_values_df.copy()
    p_values_df['p_value'] = pd.to_numeric(p_values_df['p_value'], errors='coerce')
    
    # Define conditions
    conditions = p_values_df.groupby(['sample_size', 'effect_size', 'test_type', 'hypothesis'])
    
    results = []
    
    for (sample_size, effect_size, test_type, hypothesis), group in conditions:
        total = len(group)
        if total == 0:
            continue
        
        # Count rejections
        rejections = (group['p_value'] < alpha).sum()
        
        if hypothesis == 'H0':
            # Type I error rate
            error_rate = rejections / total
            error_type = 'Type_I'
        else:
            # Type II error rate (or Power = 1 - Type II)
            error_rate = (total - rejections) / total  # Fail to reject when H1 true
            error_type = 'Type_II'
        
        results.append({
            'sample_size': sample_size,
            'effect_size': effect_size,
            'test_type': test_type,
            'hypothesis': hypothesis,
            'error_type': error_type,
            'total_iterations': total,
            'error_count': int(rejections) if hypothesis == 'H0' else int(total - rejections),
            'error_rate': float(error_rate),
            'alpha_threshold': alpha
        })
    
    return pd.DataFrame(results)

def save_aggregated_results(error_rates_df: pd.DataFrame, output_path: str) -> None:
    """
    Save aggregated error rates to CSV.
    
    Args:
        error_rates_df: DataFrame from calculate_error_rates
        output_path: Path to output CSV file
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    error_rates_df.to_csv(output_path, index=False)
    print(f"Saved aggregated error rates to {output_path}")

def main():
    """
    Main entry point for aggregation task (T018).
    Loads raw p-values, calculates error rates, and saves summary.
    """
    # Paths
    raw_pvalues_path = "data/simulation/p_values_raw.csv"
    output_path = "data/simulation/error_rates_summary.csv"
    
    # Check if raw data exists
    if not os.path.exists(raw_pvalues_path):
        print(f"Error: Raw p-values file not found at {raw_pvalues_path}")
        print("Please run the simulation first to generate p_values_raw.csv")
        return
    
    # Load raw data
    print(f"Loading raw p-values from {raw_pvalues_path}...")
    p_values_df = load_p_values_raw(raw_pvalues_path)
    
    if p_values_df is None or p_values_df.empty:
        print("Error: No data loaded from p_values_raw.csv")
        return
    
    print(f"Loaded {len(p_values_df)} records")
    
    # Calculate error rates
    print("Calculating error rates...")
    error_rates_df = calculate_error_rates(p_values_df, alpha=0.05)
    
    if error_rates_df.empty:
        print("Error: No error rates calculated. Check input data format.")
        return
    
    # Save results
    print(f"Saving aggregated results to {output_path}...")
    save_aggregated_results(error_rates_df, output_path)
    
    # Print summary
    print("\n--- Aggregation Summary ---")
    print(f"Total conditions processed: {error_rates_df['sample_size'].nunique()} sample sizes")
    print(f"Test types covered: {error_rates_df['test_type'].unique().tolist()}")
    print(f"Error types calculated: {error_rates_df['error_type'].unique().tolist()}")
    print(f"Output file: {output_path}")

if __name__ == "__main__":
    main()
