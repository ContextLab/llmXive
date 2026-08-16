"""
Aggregator module for calculating and saving aggregated error rates.

This module provides functionality to:
1. Load raw p-values from simulation output
2. Calculate empirical Type I and Type II error rates
3. Save aggregated results to CSV
"""
import os
import csv
import json
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np

from code.simulation.output_writer import load_p_values_raw
from code.simulation.logging_config import get_logger, log_operation

logger = get_logger(__name__)


def calculate_error_rates(p_values_df: pd.DataFrame, alpha: float = 0.05) -> pd.DataFrame:
    """
    Calculate empirical Type I and Type II error rates from raw p-values.
    
    Type I error: Rejecting null hypothesis when it is true (p < alpha when hypothesis_state == 'null')
    Type II error: Failing to reject null hypothesis when it is false (p > alpha when hypothesis_state == 'alternative')
    
    Args:
        p_values_df: DataFrame with columns: sample_size, effect_size, test_type, p_value, hypothesis_state
        alpha: Significance threshold (default: 0.05)
    
    Returns:
        DataFrame with aggregated error rates per condition
    """
    if p_values_df.empty:
        logger.log("error_rates_calculation_skipped", reason="empty_input")
        return pd.DataFrame()
    
    # Ensure hypothesis_state is properly typed
    p_values_df = p_values_df.copy()
    p_values_df['hypothesis_state'] = p_values_df['hypothesis_state'].astype(str)
    
    # Group by conditions
    grouped = p_values_df.groupby(['sample_size', 'effect_size', 'test_type', 'hypothesis_state'])
    
    results = []
    
    for (sample_size, effect_size, test_type, hypothesis_state), group in grouped:
        total_tests = len(group)
        p_values = group['p_value'].values
        
        if hypothesis_state == 'null':
            # Type I error: proportion of p < alpha when null is true
            type_i_errors = np.sum(p_values < alpha)
            type_i_rate = type_i_errors / total_tests if total_tests > 0 else 0.0
            
            results.append({
                'sample_size': sample_size,
                'effect_size': effect_size,
                'test_type': test_type,
                'hypothesis_state': hypothesis_state,
                'total_tests': total_tests,
                'type_i_errors': type_i_errors,
                'type_i_rate': type_i_rate,
                'type_ii_errors': None,
                'type_ii_rate': None,
                'power': None
            })
            
        elif hypothesis_state == 'alternative':
            # Type II error: proportion of p > alpha when alternative is true
            # Power = 1 - Type II error rate
            type_ii_errors = np.sum(p_values >= alpha)
            type_ii_rate = type_ii_errors / total_tests if total_tests > 0 else 0.0
            power = 1.0 - type_ii_rate
            
            results.append({
                'sample_size': sample_size,
                'effect_size': effect_size,
                'test_type': test_type,
                'hypothesis_state': hypothesis_state,
                'total_tests': total_tests,
                'type_i_errors': None,
                'type_i_rate': None,
                'type_ii_errors': type_ii_errors,
                'type_ii_rate': type_ii_rate,
                'power': power
            })
    
    result_df = pd.DataFrame(results)
    
    # Fill NaN with 0 for cleaner output
    numeric_cols = ['type_i_errors', 'type_i_rate', 'type_ii_errors', 'type_ii_rate', 'power']
    for col in numeric_cols:
        if col in result_df.columns:
            result_df[col] = result_df[col].fillna(0)
    
    return result_df


def save_aggregated_results(error_rates_df: pd.DataFrame, output_path: str) -> bool:
    """
    Save aggregated error rates to CSV file.
    
    Args:
        error_rates_df: DataFrame with error rate calculations
        output_path: Path to save the CSV file
    
    Returns:
        True if successful, False otherwise
    """
    if error_rates_df.empty:
        logger.log("save_aggregated_results_skipped", reason="empty_dataframe", output_path=output_path)
        return False
    
    try:
        # Ensure output directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            logger.log("directory_created", path=output_dir)
        
        # Save to CSV
        error_rates_df.to_csv(output_path, index=False)
        logger.log("aggregated_results_saved", 
                  path=output_path, 
                  rows=len(error_rates_df),
                  columns=list(error_rates_df.columns))
        
        return True
        
    except Exception as e:
        logger.log("save_aggregated_results_failed", 
                  error=str(e), 
                  output_path=output_path)
        return False


def load_error_rates(input_path: str) -> Optional[pd.DataFrame]:
    """
    Load aggregated error rates from CSV file.
    
    Args:
        input_path: Path to the CSV file
    
    Returns:
        DataFrame with error rates, or None if loading fails
    """
    try:
        if not os.path.exists(input_path):
            logger.log("load_error_rates_file_not_found", path=input_path)
            return None
        
        df = pd.read_csv(input_path)
        logger.log("error_rates_loaded", path=input_path, rows=len(df))
        return df
        
    except Exception as e:
        logger.log("load_error_rates_failed", error=str(e), path=input_path)
        return None


@log_operation
def main(alpha: float = 0.05, 
         input_path: Optional[str] = None, 
         output_path: Optional[str] = None) -> bool:
    """
    Main function to run the aggregation pipeline.
    
    This function:
    1. Loads raw p-values from simulation output
    2. Calculates Type I and Type II error rates
    3. Saves aggregated results to CSV
    
    Args:
        alpha: Significance threshold (default: 0.05)
        input_path: Path to raw p-values CSV (default: data/simulation/p_values_raw.csv)
        output_path: Path to save aggregated results (default: data/simulation/error_rates_summary.csv)
    
    Returns:
        True if successful, False otherwise
    """
    # Set default paths
    if input_path is None:
        input_path = "data/simulation/p_values_raw.csv"
    if output_path is None:
        output_path = "data/simulation/error_rates_summary.csv"
    
    logger.log("aggregation_start", 
              alpha=alpha, 
              input_path=input_path, 
              output_path=output_path)
    
    # Load raw p-values
    p_values_df = load_p_values_raw(input_path)
    
    if p_values_df is None or p_values_df.empty:
        logger.log("aggregation_failed", reason="no_input_data", input_path=input_path)
        return False
    
    logger.log("input_data_loaded", rows=len(p_values_df))
    
    # Calculate error rates
    error_rates_df = calculate_error_rates(p_values_df, alpha=alpha)
    
    if error_rates_df.empty:
        logger.log("aggregation_failed", reason="no_results_calculated")
        return False
    
    logger.log("error_rates_calculated", rows=len(error_rates_df))
    
    # Save results
    success = save_aggregated_results(error_rates_df, output_path)
    
    if success:
        logger.log("aggregation_complete", output_path=output_path)
    else:
        logger.log("aggregation_failed", reason="save_error", output_path=output_path)
    
    return success


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Calculate and save aggregated error rates")
    parser.add_argument("--alpha", type=float, default=0.05, help="Significance threshold")
    parser.add_argument("--input", type=str, default=None, help="Input CSV path")
    parser.add_argument("--output", type=str, default=None, help="Output CSV path")
    
    args = parser.parse_args()
    
    success = main(alpha=args.alpha, input_path=args.input, output_path=args.output)
    exit(0 if success else 1)