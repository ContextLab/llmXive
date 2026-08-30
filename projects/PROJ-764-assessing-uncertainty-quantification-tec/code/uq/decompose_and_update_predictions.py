"""
T022b: Update uq_predictions.csv with aleatoric, epistemic, total, and uncertainty_type columns.

This script consumes the output from T016 (results/uq_predictions.csv) and the logic
defined in T022a (code/uq/metrics.py) to populate the uncertainty decomposition columns.

Logic (from T022a):
- Epistemic variance = variance of means across samples (ensemble variance)
- Aleatoric variance = mean of predicted variances (average heteroscedastic noise)
- Total = Aleatoric + Epistemic
- For Sparse GP: aleatoric/epistemic are NULL, total = variance, uncertainty_type = 'total'
- For Deep Ensemble/MC-Dropout: uncertainty_type = 'decomposed'
"""
import os
import sys
import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/uq_decomposition.log')
    ]
)
logger = logging.getLogger(__name__)

def decompose_uncertainty(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply the uncertainty decomposition logic to the predictions dataframe.
    
    Args:
        df: DataFrame with columns: sample_id, method, prediction, variance, 
            lower_50, upper_50, lower_90, upper_90, aleatoric, epistemic, total, uncertainty_type
    
    Returns:
        DataFrame with populated aleatoric, epistemic, total, and uncertainty_type columns.
    """
    logger.info("Starting uncertainty decomposition for T022b")
    
    # Initialize columns with NaN (representing NULL)
    df['aleatoric'] = np.nan
    df['epistemic'] = np.nan
    df['total'] = np.nan
    df['uncertainty_type'] = None
    
    # Group by method to apply logic per technique
    methods = df['method'].unique()
    
    for method in methods:
        mask = df['method'] == method
        method_df = df.loc[mask]
        
        logger.info(f"Processing method: {method}")
        
        if method == 'sparse_gp':
            # For Sparse GP: aleatoric and epistemic are NULL, total = variance
            logger.info(f"  Applying Sparse GP logic: total = variance, aleatoric/epistemic = NULL")
            
            df.loc[mask, 'total'] = method_df['variance']
            df.loc[mask, 'uncertainty_type'] = 'total'
            
        elif method in ['deep_ensemble', 'mc_dropout']:
            # For Deep Ensemble and MC-Dropout:
            # Epistemic = variance of means across samples
            # Aleatoric = mean of predicted variances
            # Total = Aleatoric + Epistemic
            
            predictions = method_df['prediction'].values
            variances = method_df['variance'].values
            
            # Epistemic: Variance of the predictions (means) across the dataset
            epistemic_value = float(np.var(predictions, ddof=0))
            
            # Aleatoric: Mean of the predicted variances (heteroscedastic noise)
            aleatoric_value = float(np.mean(variances))
            
            # Total uncertainty
            total_value = aleatoric_value + epistemic_value
            
            logger.info(f"  Method: {method}")
            logger.info(f"    Epistemic (var of means): {epistemic_value:.6f}")
            logger.info(f"    Aleatoric (mean var): {aleatoric_value:.6f}")
            logger.info(f"    Total: {total_value:.6f}")
            
            # Assign values to all rows for this method
            df.loc[mask, 'epistemic'] = epistemic_value
            df.loc[mask, 'aleatoric'] = aleatoric_value
            df.loc[mask, 'total'] = total_value
            df.loc[mask, 'uncertainty_type'] = 'decomposed'
        else:
            logger.warning(f"  Unknown method '{method}'. Skipping decomposition.")
    
    return df

def main():
    """Main entry point for T022b."""
    input_path = Path("results/uq_predictions.csv")
    output_path = Path("results/uq_predictions.csv")
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    logger.info(f"Loading predictions from {input_path}")
    df = pd.read_csv(input_path)
    
    # Verify required columns exist
    required_cols = ['sample_id', 'method', 'prediction', 'variance']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        logger.error(f"Missing required columns in input: {missing_cols}")
        sys.exit(1)
    
    # Perform decomposition
    df_updated = decompose_uncertainty(df)
    
    # Save updated dataframe
    logger.info(f"Saving updated predictions to {output_path}")
    df_updated.to_csv(output_path, index=False)
    
    # Log summary
    logger.info("Decomposition complete. Summary:")
    for method in df_updated['method'].unique():
        row = df_updated[df_updated['method'] == method].iloc[0]
        logger.info(f"  {method}: type={row['uncertainty_type']}, "
                    f"aleatoric={row['aleatoric']}, epistemic={row['epistemic']}, "
                    f"total={row['total']}")
    
    logger.info("T022b completed successfully.")

if __name__ == "__main__":
    main()