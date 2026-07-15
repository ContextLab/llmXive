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

logger = get_logger("aggregator")

def calculate_error_rates(p_values: List[Dict[str, Any]], alpha: float = 0.05) -> List[Dict[str, Any]]:
    """
    Calculate error rates from p-values.
    Type I error: p < alpha when null is true (hypothesis='null')
    Type II error: p > alpha when alt is true (hypothesis='alternative')
    """
    results = []
    
    # Group by test_type, sample_size, effect_size, hypothesis
    df = pd.DataFrame(p_values)
    if df.empty:
        return results
    
    grouped = df.groupby(['test_type', 'sample_size', 'effect_size', 'hypothesis'])
    
    for (test_type, sample_size, effect_size, hypothesis), group in grouped:
        p_vals = group['p_value'].dropna()
        if len(p_vals) == 0:
            continue
        
        if hypothesis == 'null':
            # Type I error rate
            error_rate = (p_vals < alpha).mean()
            error_type = "Type_I"
        else:
            # Type II error rate (or 1 - power)
            error_rate = (p_vals > alpha).mean()
            error_type = "Type_II"
        
        results.append({
            "test_type": test_type,
            "sample_size": int(sample_size),
            "effect_size": float(effect_size),
            "hypothesis": hypothesis,
            "error_type": error_type,
            "error_rate": float(error_rate),
            "n_iterations": len(p_vals),
            "alpha": alpha
        })
    
    return results

def save_aggregated_results(p_values: List[Dict[str, Any]], alpha: float = 0.05, filepath: str = "data/simulation/error_rates_summary.csv"):
    """
    Save aggregated error rates to CSV.
    """
    results = calculate_error_rates(p_values, alpha)
    
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    df = pd.DataFrame(results)
    df.to_csv(filepath, index=False)
    
    logger.log("aggregated_results_saved", path=filepath, count=len(results))
    return results

def main():
    """Main entry point."""
    logger.log("start_aggregation")
    p_values = load_p_values_raw()
    if p_values:
        save_aggregated_results(p_values)
    else:
        logger.log("no_p_values_to_aggregate")

if __name__ == "__main__":
    main()
