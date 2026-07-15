import os
import csv
import json
from typing import List, Dict, Any, Optional
import pandas as pd
from code.simulation.output_writer import load_p_values_raw
from code.simulation.logging_config import get_logger

logger = get_logger(__name__)

def calculate_error_rates(p_values_data: List[Dict[str, Any]], alpha: float = 0.05) -> List[Dict[str, Any]]:
    """
    Calculate empirical Type I and Type II error rates from raw p-values.
    
    Type I Error: p < alpha when hypothesis is 'null' (should be ~alpha)
    Type II Error: p > alpha when hypothesis is 'alternative' (1 - power)
    
    Args:
        p_values_data: List of dicts with keys: sample_size, effect_size, test_type, p_value, hypothesis
        alpha: Significance threshold (default 0.05)
        
    Returns:
        List of aggregated error rate statistics per condition
    """
    if not p_values_data:
        logger.warning("No p-values provided for error rate calculation")
        return []

    df = pd.DataFrame(p_values_data)
    
    # Ensure numeric types
    df['p_value'] = pd.to_numeric(df['p_value'], errors='coerce')
    df['sample_size'] = pd.to_numeric(df['sample_size'], errors='coerce')
    
    # Drop rows with invalid p-values
    df = df.dropna(subset=['p_value', 'sample_size'])
    
    if df.empty:
        logger.warning("No valid p-values remaining after cleaning")
        return []

    results = []
    
    # Group by condition: test_type, sample_size, effect_size
    groups = df.groupby(['test_type', 'sample_size', 'effect_size'])
    
    for (test_type, sample_size, effect_size), group in groups:
        null_mask = group['hypothesis'].str.lower() == 'null'
        alt_mask = group['hypothesis'].str.lower() == 'alternative'
        
        null_p = group.loc[null_mask, 'p_value']
        alt_p = group.loc[alt_mask, 'p_value']
        
        # Type I Error Rate: proportion of null p-values < alpha
        type1_count = (null_p < alpha).sum()
        type1_total = len(null_p)
        type1_rate = type1_count / type1_total if type1_total > 0 else 0.0
        
        # Type II Error Rate: proportion of alt p-values > alpha (1 - power)
        type2_count = (alt_p > alpha).sum()
        type2_total = len(alt_p)
        type2_rate = type2_count / type2_total if type2_total > 0 else 0.0
        
        # Power: proportion of alt p-values < alpha
        power = 1.0 - type2_rate if type2_total > 0 else 0.0
        
        results.append({
            'test_type': test_type,
            'sample_size': int(sample_size),
            'effect_size': float(effect_size),
            'type1_error_rate': type1_rate,
            'type1_count': int(type1_count),
            'type1_total': int(type1_total),
            'type2_error_rate': type2_rate,
            'type2_count': int(type2_count),
            'type2_total': int(type2_total),
            'power': power,
            'total_null_iterations': int(type1_total),
            'total_alt_iterations': int(type2_total)
        })
        
    logger.info(f"Calculated error rates for {len(results)} conditions")
    return results

def save_aggregated_results(error_rates: List[Dict[str, Any]], output_path: str) -> bool:
    """
    Save aggregated error rates to a CSV file.
    
    Args:
        error_rates: List of error rate dictionaries
        output_path: Path to output CSV file
        
    Returns:
        True if successful, False otherwise
    """
    if not error_rates:
        logger.error("No error rates to save")
        return False
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logger.info(f"Created output directory: {output_dir}")
    
    try:
        df = pd.DataFrame(error_rates)
        df.to_csv(output_path, index=False)
        logger.info(f"Saved aggregated error rates to {output_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save aggregated results: {e}")
        return False

def main():
    """
    Main entry point for the aggregator module.
    Loads raw p-values, calculates error rates, and saves the summary.
    """
    logger.info("Starting error rate aggregation")
    
    # Load raw p-values
    raw_pvalues_path = "data/simulation/p_values_raw.csv"
    
    if not os.path.exists(raw_pvalues_path):
        logger.error(f"Raw p-values file not found: {raw_pvalues_path}")
        logger.error("Run the simulation first (code/main.py) to generate p_values_raw.csv")
        return False
    
    p_values_data = load_p_values_raw(raw_pvalues_path)
    
    if not p_values_data:
        logger.error("Failed to load p-values or no data found")
        return False
    
    logger.info(f"Loaded {len(p_values_data)} p-value records")
    
    # Calculate error rates (using default alpha=0.05)
    error_rates = calculate_error_rates(p_values_data, alpha=0.05)
    
    if not error_rates:
        logger.error("No error rates calculated")
        return False
    
    # Save results
    output_path = "data/simulation/error_rates_summary.csv"
    success = save_aggregated_results(error_rates, output_path)
    
    if success:
        logger.info("Aggregation complete")
        return True
    else:
        logger.error("Aggregation failed")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
