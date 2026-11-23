"""
Task T013b: Check Collinearity (VIF Calculation)

Calculates Variance Inflation Factor (VIF) for each CRE by regressing the signal
of one TF against all other TFs binding that specific CRE.

Input: data/processed/peak_signal_matrix.tsv
Output: data/processed/vif_flags.tsv

Depends on: T007c (peak_signal_matrix.tsv), T008 (CRE definitions)
"""

import os
import sys
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import pandas as pd
import numpy as np
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.tools.tools import add_constant

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/pipeline.log')
    ]
)
logger = logging.getLogger(__name__)

def load_peak_signal_matrix(input_path: str) -> pd.DataFrame:
    """
    Load the peak signal matrix from T007c.
    Expected columns: cre_id, tf_id, condition, signal
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    logger.info(f"Loading peak signal matrix from {input_path}")
    df = pd.read_csv(path, sep='\t')
    
    required_cols = {'cre_id', 'tf_id', 'condition', 'signal'}
    if not required_cols.issubset(df.columns):
        missing = required_cols - set(df.columns)
        raise ValueError(f"Missing required columns in {input_path}: {missing}")
    
    logger.info(f"Loaded {len(df)} rows. Unique CREs: {df['cre_id'].nunique()}, Unique TFs: {df['tf_id'].nunique()}")
    return df

def calculate_vif_for_cre(signal_matrix: pd.DataFrame, cre_id: str, vif_threshold: float = 5.0) -> Tuple[str, float, bool]:
    """
    Calculate VIF for a specific CRE.
    
    Strategy:
    1. Filter rows for the specific cre_id.
    2. Pivot to wide format: rows = conditions, cols = TFs, values = signal.
    3. If < 2 TFs bind this CRE, VIF is undefined (set to 0.0, not collinear).
    4. Calculate VIF for each TF column using the other TF columns as predictors.
    5. Return the MAXIMUM VIF observed for this CRE.
    """
    cre_data = signal_matrix[signal_matrix['cre_id'] == cre_id]
    
    # Pivot to wide format: index=condition, columns=tf_id, values=signal
    # Drop rows where any TF is missing signal (NaN) to ensure valid regression
    wide_data = cre_data.pivot(index='condition', columns='tf_id', values='signal')
    
    if wide_data.empty:
        return cre_id, 0.0, False
    
    # Drop rows with any NaN (incomplete data for this CRE across conditions)
    wide_data = wide_data.dropna()
    
    if wide_data.shape[1] < 2:
        # Not enough predictors to calculate VIF (need at least 2 variables)
        # If only 1 TF binds, no collinearity exists by definition
        return cre_id, 0.0, False
    
    # Prepare matrix X for regression
    # We calculate VIF for each column in X
    X = wide_data.values
    
    # Add constant for intercept
    X_with_const = add_constant(X)
    
    vifs = []
    # Calculate VIF for each feature (excluding the constant column)
    # VIF_j = 1 / (1 - R_j^2) where R_j^2 is from regressing feature j on all other features
    for i in range(1, X_with_const.shape[1]):
        try:
            vif_val = variance_inflation_factor(X_with_const, i)
            if np.isfinite(vif_val):
                vifs.append(vif_val)
            else:
                vifs.append(0.0) # Treat non-finite as 0
        except Exception as e:
            logger.warning(f"Could not calculate VIF for TF index {i} in CRE {cre_id}: {e}")
            vifs.append(0.0)
    
    if not vifs:
        max_vif = 0.0
    else:
        max_vif = max(vifs)
    
    is_collinear = max_vif > vif_threshold
    return cre_id, max_vif, is_collinear

def compute_all_vifs(signal_matrix: pd.DataFrame, vif_threshold: float = 5.0) -> pd.DataFrame:
    """
    Compute VIF for all unique CREs in the dataset.
    """
    cre_ids = signal_matrix['cre_id'].unique()
    results = []
    
    total = len(cre_ids)
    logger.info(f"Starting VIF calculation for {total} CREs...")
    
    for idx, cre_id in enumerate(cre_ids):
        cre_id, vif_score, is_collinear = calculate_vif_for_cre(signal_matrix, cre_id, vif_threshold)
        results.append({
            'cre_id': cre_id,
            'vif_score': vif_score,
            'is_collinear': is_collinear
        })
        
        if (idx + 1) % 1000 == 0:
            logger.info(f"Processed {idx + 1}/{total} CREs")
    
    df_results = pd.DataFrame(results)
    return df_results

def write_output(df: pd.DataFrame, output_path: str) -> None:
    """
    Write the VIF flags to a TSV file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Writing VIF flags to {output_path}")
    df.to_csv(path, sep='\t', index=False)
    
    # Log summary
    collinear_count = df['is_collinear'].sum()
    total_count = len(df)
    logger.info(f"VIF calculation complete. Total CREs: {total_count}, Collinear (VIF > 5): {collinear_count}")

def main():
    parser = argparse.ArgumentParser(description='Calculate VIF for CREs to detect collinearity.')
    parser.add_argument('--input', '-i', type=str, required=True, 
                        help='Path to peak_signal_matrix.tsv (output of T007c)')
    parser.add_argument('--output', '-o', type=str, required=True, 
                        help='Path to output vif_flags.tsv')
    parser.add_argument('--threshold', '-t', type=float, default=5.0,
                        help='VIF threshold for flagging collinearity (default: 5.0)')
    
    args = parser.parse_args()
    
    try:
        # 1. Load data
        signal_matrix = load_peak_signal_matrix(args.input)
        
        # 2. Compute VIFs
        vif_results = compute_all_vifs(signal_matrix, args.threshold)
        
        # 3. Write output
        write_output(vif_results, args.output)
        
        logger.info("Task T013b completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during VIF calculation: {e}")
        raise

if __name__ == '__main__':
    main()
