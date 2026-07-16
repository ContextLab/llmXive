import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple, Optional
import logging
import csv
import os

logger = logging.getLogger(__name__)

def run_sensitivity_sweep(csv_path: str, config: Any) -> pd.DataFrame:
    """
    Run a sensitivity sweep over the scaling factors.
    Reads existing results, perturbs scaling factors, and recalculates conductivity.
    
    Args:
        csv_path: Path to the simulation results CSV.
        config: Simulation config object.
        
    Returns:
        DataFrame with sensitivity results.
    """
    # Load existing data
    df = pd.read_csv(csv_path)
    
    # Define perturbation range (e.g., +/- 10%)
    perturbations = [-0.1, 0.0, 0.1]
    
    sensitivity_data = []
    
    for idx, row in df.iterrows():
        if pd.isna(row['conductivity']) or row['conductivity'] == 0:
            continue
            
        base_k = row['conductivity']
        base_fs = row['scaling_factor']
        
        for delta in perturbations:
            # Perturb the scaling factor
            new_fs = base_fs * (1.0 + delta)
            
            # Recalculate conductivity (simplified model: k scales linearly with fs)
            # In a full implementation, this would re-run the solver
            new_k = base_k * (new_fs / base_fs)
            
            sensitivity_data.append({
                'seed': row['seed'],
                'N': row['N'],
                'p': row['p'],
                'perturbation': delta,
                'original_k': base_k,
                'perturbed_k': new_k,
                'deviation': abs(new_k - base_k) / base_k if base_k != 0 else 0
            })
            
    return pd.DataFrame(sensitivity_data)

def calculate_deviation_report(sensitivity_df: pd.DataFrame) -> Dict[str, float]:
    """
    Calculate summary statistics for the sensitivity analysis.
    
    Args:
        sensitivity_df: DataFrame from run_sensitivity_sweep.
        
    Returns:
        Dictionary with mean, max, and min deviation.
    """
    if sensitivity_df.empty:
        return {'mean_deviation': 0.0, 'max_deviation': 0.0, 'min_deviation': 0.0}
        
    deviations = sensitivity_df['deviation'].values
    
    return {
        'mean_deviation': float(np.mean(deviations)),
        'max_deviation': float(np.max(deviations)),
        'min_deviation': float(np.min(deviations))
    }

def report_sensitivity_results(csv_path: str, sensitivity_df: pd.DataFrame, report: Dict[str, float]) -> None:
    """
    Update the main CSV with sensitivity metrics.
    
    Args:
        csv_path: Path to the simulation results CSV.
        sensitivity_df: DataFrame from run_sensitivity_sweep.
        report: Deviation report dictionary.
    """
    # Read the main CSV
    df = pd.read_csv(csv_path)
    
    # Aggregate sensitivity metrics per seed (if multiple runs per seed exist)
    # For simplicity, we take the max deviation for each seed from the sweep
    agg_sensitivity = sensitivity_df.groupby('seed')['deviation'].max().reset_index()
    agg_sensitivity.columns = ['seed', 'sensitivity_deviation']
    
    # Merge back to main DF
    df = df.merge(agg_sensitivity, on='seed', how='left')
    
    # Fill missing with 0 if no sensitivity run
    df['sensitivity_deviation'] = df['sensitivity_deviation'].fillna(0.0)
    
    # Add min/max columns (global stats for this run)
    df['sensitivity_min'] = report['min_deviation']
    df['sensitivity_max'] = report['max_deviation']
    
    # Write back
    df.to_csv(csv_path, index=False)
    logger.info(f"Sensitivity metrics appended to {csv_path}")
    logger.info(f"Sensitivity Report: Mean={report['mean_deviation']:.4f}, Max={report['max_deviation']:.4f}")
