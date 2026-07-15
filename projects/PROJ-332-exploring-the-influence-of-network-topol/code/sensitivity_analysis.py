import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple, Optional
import logging
import csv
import os

logger = logging.getLogger(__name__)

def run_sensitivity_sweep(
    base_params: Dict[str, Any], 
    param_to_sweep: str, 
    sweep_values: List[float],
    simulation_func: callable
) -> List[Dict[str, Any]]:
    """
    Run a sensitivity sweep over a specific parameter.
    
    Args:
        base_params: Dictionary of base simulation parameters.
        param_to_sweep: Name of the parameter to vary.
        sweep_values: List of values to test.
        simulation_func: Function to run the simulation (should accept params).
    
    Returns:
        List of result dictionaries for each sweep point.
    """
    results = []
    for value in sweep_values:
        current_params = base_params.copy()
        current_params[param_to_sweep] = value
        try:
            # Call the simulation function
            res = simulation_func(current_params)
            res['sensitivity_param_name'] = param_to_sweep
            res['sensitivity_param_value'] = value
            results.append(res)
        except Exception as e:
            logger.error(f"Sensitivity sweep failed for {param_to_sweep}={value}: {e}")
    return results

def report_sensitivity_results(stats: Dict[str, Any]):
    """
    Log and print sensitivity analysis results.
    
    Args:
        stats: Dictionary containing sensitivity statistics (mean, std, CV, etc.)
    """
    logger.info("=== Sensitivity Analysis Report ===")
    logger.info(f"Mean Conductivity: {stats.get('mean', 0):.4f} W/(m·K)")
    logger.info(f"Std Deviation: {stats.get('std', 0):.4f} W/(m·K)")
    logger.info(f"Coefficient of Variation (CV): {stats.get('cv', 0):.4f}")
    logger.info(f"Min Conductivity: {stats.get('min', 0):.4f} W/(m·K)")
    logger.info(f"Max Conductivity: {stats.get('max', 0):.4f} W/(m·K)")
    
    # Check if variations are within ±10% (SC-004)
    cv = stats.get('cv', 0)
    if cv <= 0.10:
        logger.info("Sensitivity check PASSED: Variations within ±10% (CV ≤ 0.10).")
    else:
        logger.warning(f"Sensitivity check FAILED: Variations exceed ±10% (CV = {cv:.4f}).")

def analyze_sensitivity(df: pd.DataFrame, target_col: str) -> Dict[str, Any]:
    """
    Analyze the sensitivity of a target column across a sweep.
    
    Args:
        df: DataFrame containing the sweep results.
        target_col: Name of the column to analyze (e.g., 'conductivity').
    
    Returns:
        Dictionary with sensitivity statistics.
    """
    if df.empty:
        return {}
    
    values = df[target_col].dropna()
    if len(values) == 0:
        return {}
    
    mean_val = values.mean()
    std_val = values.std()
    min_val = values.min()
    max_val = values.max()
    cv = std_val / mean_val if mean_val != 0 else 0.0
    
    stats = {
        'mean': mean_val,
        'std': std_val,
        'min': min_val,
        'max': max_val,
        'cv': cv,
        'count': len(values)
    }
    
    logger.debug(f"Sensitivity analysis stats: {stats}")
    return stats
