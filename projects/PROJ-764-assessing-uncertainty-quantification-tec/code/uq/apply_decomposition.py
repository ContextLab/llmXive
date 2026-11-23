"""
Script to execute uncertainty decomposition logic on base predictions.

This script imports the decomposition logic from T022a (via metrics.py)
and populates results/uq_predictions.csv with aleatoric/epistemic breakdowns.
"""
import os
import sys
import json
import logging
import argparse
from pathlib import Path

import pandas as pd
import numpy as np

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from uq.metrics import decompose_uncertainty
from utils.logging_config import setup_logging

# Configure logging
logger = setup_logging("uq_apply_decomposition", log_file="logs/apply_decomposition.log")

def load_base_predictions(input_path: str) -> pd.DataFrame:
    """
    Load base predictions from T016a output.
    
    Expected columns: sample_id, method, prediction, variance, 
    lower_50, upper_50, lower_90, upper_90
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(
            f"Base predictions file not found at {input_path}. "
            "Ensure T016a has completed successfully."
        )
    
    df = pd.read_csv(input_path)
    required_cols = ['sample_id', 'method', 'prediction', 'variance', 
                    'lower_50', 'upper_50', 'lower_90', 'upper_90']
    
    missing = set(required_cols) - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in {input_path}: {missing}")
    
    logger.info(f"Loaded {len(df)} predictions from {input_path}")
    return df

def apply_decomposition(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply uncertainty decomposition to each row.
    
    For Deep Ensemble and MC Dropout:
      - aleatoric = mean of predicted variances
      - epistemic = variance of means across samples
      - total = aleatoric + epistemic
      - uncertainty_type = "combined"
    
    For Sparse GP:
      - aleatoric = null
      - epistemic = null
      - total = variance
      - uncertainty_type = "total"
    """
    results = []
    
    # Group by method to handle ensemble methods correctly
    for method in df['method'].unique():
        method_df = df[df['method'] == method].copy()
        
        if method == 'sparse_gp':
            # For Sparse GP, set aleatoric/epistemic to null
            method_df['aleatoric'] = np.nan
            method_df['epistemic'] = np.nan
            method_df['total'] = method_df['variance']
            method_df['uncertainty_type'] = 'total'
        else:
            # For Deep Ensemble and MC Dropout
            # We need to decompose based on the method's characteristics
            # Since we have aggregated predictions here, we apply the decomposition logic
            # The decompose_uncertainty function from metrics.py handles this
            
            # Extract predictions and variances for decomposition
            predictions = method_df['prediction'].values
            variances = method_df['variance'].values
            
            # Apply decomposition logic
            # Note: For aggregated predictions, we assume the variance provided
            # is the total variance, and we need to decompose it
            # In a real ensemble, we'd have individual predictions, but here
            # we use the variance as epistemic for ensemble methods
            
            # For Deep Ensemble: variance of means = epistemic
            # For MC Dropout: variance of stochastic passes = epistemic
            # The variance column already contains this for our aggregated data
            
            # Calculate aleatoric as a fraction (simplified approach)
            # In practice, aleatoric would come from heteroscedastic head predictions
            # Here we estimate: aleatoric = variance * (1 - epistemic_ratio)
            # For simplicity, we'll use the variance as epistemic for ensemble methods
            # and set aleatoric to 0 or estimate from prediction magnitude
            
            # Better approach: use the decompose_uncertainty function
            decomposed = decompose_uncertainty(
                predictions=predictions,
                variances=variances,
                method=method
            )
            
            method_df['aleatoric'] = decomposed['aleatoric']
            method_df['epistemic'] = decomposed['epistemic']
            method_df['total'] = decomposed['total']
            method_df['uncertainty_type'] = 'combined'
        
        results.append(method_df)
    
    result_df = pd.concat(results, ignore_index=True)
    return result_df

def save_predictions(df: pd.DataFrame, output_path: str):
    """
    Save predictions with decomposition to CSV.
    
    Uses na_rep='' to handle null values for Sparse GP.
    """
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save with na_rep='' for null handling
    df.to_csv(output_path, index=False, na_rep='')
    logger.info(f"Saved {len(df)} predictions to {output_path}")

def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Apply uncertainty decomposition to base predictions"
    )
    parser.add_argument(
        "--input",
        type=str,
        default="results/uq_predictions_base.csv",
        help="Path to base predictions CSV (from T016a)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="results/uq_predictions.csv",
        help="Path to output CSV with decomposition"
    )
    args = parser.parse_args()
    
    try:
        # Load base predictions
        df = load_base_predictions(args.input)
        
        # Apply decomposition
        df_decomposed = apply_decomposition(df)
        
        # Save results
        save_predictions(df_decomposed, args.output)
        
        logger.info("Uncertainty decomposition completed successfully")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())