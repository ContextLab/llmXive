"""
Sensitivity comparison module.
Compares interaction coefficients between baseline and sensitivity models.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

def load_baseline_results(file_path: str = "data/results/regression_results.csv") -> pd.DataFrame:
    """Load baseline regression results."""
    path = Path(file_path)
    if not path.exists():
        logger.warning(f"Baseline results not found: {path}")
        return pd.DataFrame()
    return pd.read_csv(path)

def load_sensitivity_results(file_path: str = "data/results/sensitivity_analysis.csv") -> pd.DataFrame:
    """Load sensitivity analysis results."""
    path = Path(file_path)
    if not path.exists():
        logger.warning(f"Sensitivity results not found: {path}")
        return pd.DataFrame()
    return pd.read_csv(path)

def extract_interaction_coefficients(results_df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract interaction coefficients from results DataFrame.
    
    Args:
        results_df: DataFrame containing model results
        
    Returns:
        DataFrame with outcome, model_type, and interaction_coef
    """
    if results_df.empty:
        return pd.DataFrame(columns=['outcome', 'model_type', 'interaction_coef', 'interaction_p'])
    
    # Check for pre-computed interaction columns
    if 'interaction_coef' in results_df.columns:
        return results_df[['outcome', 'model_type', 'interaction_coef', 'interaction_p']]
    
    # Otherwise, look for specific coefficient columns
    # This depends on how the results were saved
    # Fallback: try to find a column named like the interaction term
    interaction_col_name = 'social_support:harassment_exposure'
    
    if interaction_col_name in results_df.columns:
        return results_df[['outcome', 'model_type', interaction_col_name]].rename(
            columns={interaction_col_name: 'interaction_coef'}
        )
    
    # If all else fails, return empty
    logger.warning("Could not find interaction coefficient columns in results.")
    return pd.DataFrame(columns=['outcome', 'model_type', 'interaction_coef', 'interaction_p'])

def compare_coefficients(
    baseline_df: pd.DataFrame,
    sensitivity_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Compare interaction coefficients between baseline and sensitivity runs.
    
    Args:
        baseline_df: Baseline results
        sensitivity_df: Sensitivity results
        
    Returns:
        Comparison table
    """
    baseline_inter = extract_interaction_coefficients(baseline_df)
    sensitivity_inter = extract_interaction_coefficients(sensitivity_df)
    
    if baseline_inter.empty or sensitivity_inter.empty:
        logger.warning("Empty baseline or sensitivity data for comparison.")
        return pd.DataFrame()
    
    # Merge on outcome
    # We assume sensitivity runs are per-outcome or we aggregate
    # For simplicity, we'll merge on outcome and model_type if possible
    
    comparison = []
    
    for _, row in baseline_inter.iterrows():
        outcome = row['outcome']
        base_coef = row['interaction_coef']
        
        # Find matching sensitivity rows
        sens_rows = sensitivity_inter[sensitivity_inter['outcome'] == outcome]
        
        for _, sens_row in sens_rows.iterrows():
            sens_coef = sens_row['interaction_coef']
            model_type = sens_row['model_type']
            
            shift = sens_coef - base_coef
            pct_shift = (shift / base_coef * 100) if base_coef != 0 else 0
            
            comparison.append({
                'outcome': outcome,
                'baseline_coef': base_coef,
                'sensitivity_model': model_type,
                'sensitivity_coef': sens_coef,
                'absolute_shift': shift,
                'percent_shift': pct_shift
            })
    
    return pd.DataFrame(comparison)

def save_comparison_table(df: pd.DataFrame, output_path: str = "data/results/sensitivity_comparison.csv"):
    """Save comparison table to CSV."""
    if df.empty:
        logger.warning("No comparison data to save.")
        return
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved comparison table to {output_path}")

def main():
    """Main entry point for sensitivity comparison."""
    logging.basicConfig(level=logging.INFO)
    
    baseline = load_baseline_results()
    sensitivity = load_sensitivity_results()
    
    comparison = compare_coefficients(baseline, sensitivity)
    save_comparison_table(comparison)
    
    return comparison

if __name__ == "__main__":
    main()