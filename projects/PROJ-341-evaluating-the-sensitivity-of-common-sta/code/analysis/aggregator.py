"""
Aggregator module for calculating and saving error rates.
Implements T017 (calculation) and T018 (saving).
"""
import os
import csv
import json
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np

# Import from existing API surface
from code.simulation.logging_config import get_logger, log_operation
from code.simulation.output_writer import load_p_values_raw_safe

logger = get_logger(__name__)

def calculate_error_rates(p_values_df: pd.DataFrame, alpha: float = 0.05) -> pd.DataFrame:
    """
    Calculate empirical Type I and Type II error rates from raw p-values.
    
    Args:
        p_values_df: DataFrame with columns: sample_size, effect_size, test_type, 
                     hypothesis, p_value (and potentially others)
        alpha: Significance threshold (default 0.05)
    
    Returns:
        DataFrame with aggregated error rates per condition
    """
    if p_values_df.empty:
        logger.log("calculate_error_rates", status="empty_input")
        return pd.DataFrame()

    # Ensure hypothesis column exists and is clean
    if 'hypothesis' not in p_values_df.columns:
        # Default to 'H1' if missing (though spec implies it should exist)
        p_values_df = p_values_df.copy()
        p_values_df['hypothesis'] = 'H1'

    # Group by conditions
    group_cols = ['sample_size', 'effect_size', 'test_type', 'hypothesis']
    # Filter to only existing columns
    existing_group_cols = [c for c in group_cols if c in p_values_df.columns]
    
    if not existing_group_cols:
        logger.log("calculate_error_rates", status="missing_group_columns", columns=list(p_values_df.columns))
        return pd.DataFrame()

    results = []

    for name, group in p_values_df.groupby(existing_group_cols):
        p_vals = group['p_value'].values
        n = len(p_vals)
        
        if n == 0:
            continue

        # Determine hypothesis state
        is_null_true = (name[-1] if len(name) == len(group_cols) else group.iloc[0]['hypothesis']) == 'H0'
        
        # Calculate errors
        # Type I error: Reject H0 when H0 is true (p < alpha)
        # Type II error: Fail to reject H0 when H1 is true (p > alpha)
        
        if is_null_true:
            # Under H0: proportion of p < alpha is empirical Type I error rate
            type_i_rate = np.mean(p_vals < alpha)
            type_ii_rate = np.nan  # Not applicable under H0
            power = 1.0 - type_ii_rate if not np.isnan(type_ii_rate) else np.nan
        else:
            # Under H1: proportion of p > alpha is empirical Type II error rate
            type_ii_rate = np.mean(p_vals > alpha)
            type_i_rate = np.nan  # Not applicable under H1
            power = 1.0 - type_ii_rate

        results.append({
            'sample_size': name[0] if len(name) > 0 else np.nan,
            'effect_size': name[1] if len(name) > 1 else np.nan,
            'test_type': name[2] if len(name) > 2 else np.nan,
            'hypothesis': name[3] if len(name) > 3 else np.nan,
            'n_iterations': n,
            'type_i_error_rate': type_i_rate,
            'type_ii_error_rate': type_ii_rate,
            'power': power,
            'alpha_threshold': alpha
        })

    result_df = pd.DataFrame(results)
    
    if not result_df.empty:
        # Ensure numeric columns are numeric
        numeric_cols = ['sample_size', 'effect_size', 'n_iterations', 
                        'type_i_error_rate', 'type_ii_error_rate', 'power']
        for col in numeric_cols:
            if col in result_df.columns:
                result_df[col] = pd.to_numeric(result_df[col], errors='coerce')

    return result_df

def save_aggregated_results(error_rates_df: pd.DataFrame, output_path: str, alpha: float = 0.05) -> bool:
    """
    Save aggregated error rates to CSV file (T018).
    
    Args:
        error_rates_df: DataFrame with error rate calculations
        output_path: Path to save the CSV file
        alpha: Alpha threshold used (for metadata)
    
    Returns:
        True if successful, False otherwise
    """
    if error_rates_df.empty:
        logger.log("save_aggregated_results", status="empty_dataframe", output_path=output_path)
        return False

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logger.log("save_aggregated_results", action="created_directory", path=output_dir)

    try:
        # Save to CSV
        error_rates_df.to_csv(output_path, index=False)
        
        # Log success
        logger.log("save_aggregated_results", 
                   status="success", 
                   output_path=output_path,
                   rows=len(error_rates_df),
                   columns=list(error_rates_df.columns))
        
        return True
    except Exception as e:
        logger.log("save_aggregated_results", status="failed", error=str(e), output_path=output_path)
        return False

def main():
    """
    Main entry point for T017/T018: Load raw p-values, calculate error rates, save summary.
    """
    # Configuration
    input_path = "data/simulation/p_values_raw.csv"
    output_path = "data/simulation/error_rates_summary.csv"
    alpha = 0.05

    logger.log("aggregator_main", action="starting", input=input_path, output=output_path)

    # Load raw p-values
    if not os.path.exists(input_path):
        logger.log("aggregator_main", status="failed", reason="input_file_not_found", path=input_path)
        print(f"Error: Input file not found: {input_path}")
        return 1

    try:
        p_values_df = load_p_values_raw_safe(input_path)
        if p_values_df is None or p_values_df.empty:
            logger.log("aggregator_main", status="failed", reason="no_data_loaded")
            print(f"Error: Could not load or no data in: {input_path}")
            return 1
    except Exception as e:
        logger.log("aggregator_main", status="failed", reason="load_error", error=str(e))
        print(f"Error loading p-values: {e}")
        return 1

    # Calculate error rates
    error_rates_df = calculate_error_rates(p_values_df, alpha=alpha)
    
    if error_rates_df.empty:
        logger.log("aggregator_main", status="failed", reason="no_error_rates_calculated")
        print("Error: No error rates could be calculated.")
        return 1

    # Save results
    success = save_aggregated_results(error_rates_df, output_path, alpha=alpha)
    
    if not success:
        logger.log("aggregator_main", status="failed", reason="save_failed")
        print("Error: Failed to save aggregated results.")
        return 1

    print(f"Successfully saved error rates to {output_path}")
    print(f"Summary: {len(error_rates_df)} conditions analyzed")
    print(error_rates_df.describe())
    
    logger.log("aggregator_main", status="completed", output=output_path, rows=len(error_rates_df))
    return 0

if __name__ == "__main__":
    exit(main())