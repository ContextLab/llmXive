import os
import sys
import logging
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Add project root to path if running as script
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.visualization.plots import load_processed_data, load_predictions
from code.config import RANDOM_SEED

logger = logging.getLogger(__name__)

def identify_failure_regimes(
    df_processed: pd.DataFrame,
    df_predictions: pd.DataFrame,
    error_threshold: float = 2.0,
    strain_rate_threshold: float = 1000.0,
    alloy_families: List[str] = None
) -> pd.DataFrame:
    """
    Identify failure regimes where empirical models significantly underperform ML models.
    
    A failure regime is defined as:
    1. High strain rate (> strain_rate_threshold)
    2. Specific alloy families where empirical model error > error_threshold * ML model error
    3. Regions where empirical model predictions deviate significantly from observed data
    
    Args:
        df_processed: Processed dataset with actual yield strengths
        df_predictions: DataFrame with ML and empirical model predictions
        error_threshold: Multiplier for acceptable error ratio (default: 2.0)
        strain_rate_threshold: Minimum strain rate to consider as high (default: 1000 s^-1)
        alloy_families: Specific families to analyze (default: all in data)
        
    Returns:
        DataFrame with identified failure regimes
    """
    if df_predictions is None or df_processed is None:
        logger.warning("No data provided for failure regime identification")
        return pd.DataFrame()
    
    # Merge processed data with predictions
    df_merged = df_processed.merge(
        df_predictions,
        on=['sample_id', 'alloy_family', 'strain_rate_s_inv', 'temperature_k'],
        how='inner'
    )
    
    if df_merged.empty:
        logger.warning("No matching records found between processed data and predictions")
        return pd.DataFrame()
    
    # Calculate errors
    # Assuming columns: 'yield_strength_mpa' (actual), 'pred_ml', 'pred_empirical'
    actual_col = 'yield_strength_mpa'
    ml_pred_col = 'pred_ml'
    emp_pred_col = 'pred_empirical'
    
    if not all(col in df_merged.columns for col in [actual_col, ml_pred_col, emp_pred_col]):
        # Try alternative column names
        if 'yield_strength_mpa' in df_merged.columns and 'ml_prediction' in df_merged.columns:
            ml_pred_col = 'ml_prediction'
        if 'empirical_prediction' in df_merged.columns:
            emp_pred_col = 'empirical_prediction'
        
        if not all(col in df_merged.columns for col in [actual_col, ml_pred_col, emp_pred_col]):
            logger.error(f"Required prediction columns not found. Available: {df_merged.columns.tolist()}")
            return pd.DataFrame()
    
    df_merged['abs_error_ml'] = np.abs(df_merged[actual_col] - df_merged[ml_pred_col])
    df_merged['abs_error_empirical'] = np.abs(df_merged[actual_col] - df_merged[emp_pred_col])
    df_merged['error_ratio'] = df_merged['abs_error_empirical'] / (df_merged['abs_error_ml'] + 1e-6)
    
    # Identify failure regimes
    # Criterion 1: High strain rate
    high_strain_rate_mask = df_merged['strain_rate_s_inv'] > strain_rate_threshold
    
    # Criterion 2: Empirical model error significantly higher than ML
    high_error_ratio_mask = df_merged['error_ratio'] > error_threshold
    
    # Criterion 3: Absolute empirical error above a threshold (e.g., 50 MPa)
    high_absolute_error_mask = df_merged['abs_error_empirical'] > 50.0
    
    # Combine criteria: failure regime if high strain rate AND (high error ratio OR high absolute error)
    failure_mask = high_strain_rate_mask & (high_error_ratio_mask | high_absolute_error_mask)
    
    df_failures = df_merged[failure_mask].copy()
    
    if df_failures.empty:
        logger.info("No failure regimes identified with current thresholds")
        return pd.DataFrame()
    
    # Group by alloy family and strain rate bins to identify specific regimes
    df_failures['strain_rate_bin'] = pd.cut(
        df_failures['strain_rate_s_inv'],
        bins=[0, 100, 1000, 10000, 100000, float('inf')],
        labels=['<100', '100-1k', '1k-10k', '10k-100k', '>100k']
    )
    
    regime_summary = df_failures.groupby(['alloy_family', 'strain_rate_bin']).agg({
        'sample_id': 'count',
        'abs_error_empirical': 'mean',
        'abs_error_ml': 'mean',
        'error_ratio': 'mean',
        'yield_strength_mpa': ['mean', 'std']
    }).reset_index()
    
    # Flatten column names
    regime_summary.columns = [
        'alloy_family', 'strain_rate_bin', 'n_samples',
        'mean_empirical_error', 'mean_ml_error', 'mean_error_ratio',
        'mean_yield_strength', 'std_yield_strength'
    ]
    
    # Sort by error ratio descending
    regime_summary = regime_summary.sort_values('mean_error_ratio', ascending=False)
    
    # Add regime classification
    regime_summary['regime_type'] = regime_summary.apply(
        lambda row: f"High strain rate failure ({row['alloy_family']})" 
                    if row['strain_rate_bin'] in ['1k-10k', '10k-100k', '>100k']
                    else f"Moderate strain rate failure ({row['alloy_family']})",
        axis=1
    )
    
    return regime_summary

def save_failure_regimes(
    regimes_df: pd.DataFrame,
    output_path: str
) -> None:
    """
    Save failure regimes to CSV.
    
    Args:
        regimes_df: DataFrame with identified failure regimes
        output_path: Path to save the CSV file
    """
    if regimes_df.empty:
        # Create empty file with headers
        df_empty = pd.DataFrame(columns=[
            'alloy_family', 'strain_rate_bin', 'n_samples',
            'mean_empirical_error', 'mean_ml_error', 'mean_error_ratio',
            'mean_yield_strength', 'std_yield_strength', 'regime_type'
        ])
        df_empty.to_csv(output_path, index=False)
        logger.info(f"Saved empty failure regimes to {output_path}")
        return
    
    regimes_df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(regimes_df)} failure regimes to {output_path}")

def main():
    """Main entry point for failure regime identification."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    project_root = Path(__file__).resolve().parent.parent.parent
    data_dir = project_root / 'data' / 'processed'
    output_path = data_dir / 'failure_regimes.csv'
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # Load processed data
        logger.info("Loading processed data...")
        df_processed = load_processed_data()
        
        if df_processed is None or df_processed.empty:
            logger.warning("No processed data found. Creating empty failure regimes file.")
            save_failure_regimes(pd.DataFrame(), str(output_path))
            return
        
        # Load predictions
        logger.info("Loading model predictions...")
        df_predictions = load_predictions()
        
        if df_predictions is None or df_predictions.empty:
            logger.warning("No predictions found. Creating empty failure regimes file.")
            save_failure_regimes(pd.DataFrame(), str(output_path))
            return
        
        # Identify failure regimes
        logger.info("Identifying failure regimes...")
        regimes_df = identify_failure_regimes(
            df_processed=df_processed,
            df_predictions=df_predictions,
            error_threshold=2.0,
            strain_rate_threshold=1000.0
        )
        
        # Save results
        save_failure_regimes(regimes_df, str(output_path))
        
        if not regimes_df.empty:
            logger.info(f"Identified {len(regimes_df)} failure regimes")
            logger.info(f"Top 3 failure regimes by error ratio:\n{regimes_df.head(3)}")
        else:
            logger.info("No failure regimes identified with current thresholds")
            
    except Exception as e:
        logger.error(f"Error during failure regime identification: {e}", exc_info=True)
        # Create empty file on error
        save_failure_regimes(pd.DataFrame(), str(output_path))
        raise

if __name__ == '__main__':
    main()