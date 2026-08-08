import os
import sys
import json
import logging
import math
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from imblearn.over_sampling import SMOTE

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/resampling.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
RESULTS_DIR = Path('results')
RESAMPLING_LOG_PATH = RESULTS_DIR / 'resampling_log.json'
REAL_DATA_MAX_LOSS_THRESHOLD = 0.20  # 20%
MIN_REAL_DATA_RATIO = 0.70  # Ensure real data is at least 70% if SMOTE used
COMBINED_CV_MAX = 0.30
REAL_DATA_CV_MAX = 0.10
MINORITY_QUANTILE = 0.05

def ensure_directories():
    """Ensure required directories exist."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

def load_processed_data() -> pd.DataFrame:
    """Load the processed dataset with descriptors and targets."""
    path = Path('data/processed/descriptors.parquet')
    if not path.exists():
        raise FileNotFoundError(f"Processed data not found at {path}")
    logger.info(f"Loading processed data from {path}")
    return pd.read_parquet(path)

def calculate_cv(values: np.ndarray) -> float:
    """Calculate Coefficient of Variation (CV = std / mean)."""
    if len(values) == 0:
        return 0.0
    mean_val = np.mean(values)
    if abs(mean_val) < 1e-9:
        return float('inf')
    std_val = np.std(values)
    return std_val / abs(mean_val)

def dynamic_binning_resample(df: pd.DataFrame, target_col: str, 
                             num_bins: int = 10) -> Tuple[pd.DataFrame, float]:
    """
    Perform stratified resampling using equal-frequency binning.
    Returns resampled dataframe and the CV of the resampled target distribution.
    """
    logger.info(f"Starting dynamic binning resampling for target: {target_col}")
    
    # Create bins based on quantiles
    df = df.copy()
    df['bin_id'] = pd.qcut(df[target_col], q=num_bins, labels=False, duplicates='drop')
    
    # Resample to equal frequency per bin
    min_bin_size = df['bin_id'].value_counts().min()
    resampled_dfs = []
    
    for bin_id in df['bin_id'].unique():
        bin_data = df[df['bin_id'] == bin_id]
        if len(bin_data) > min_bin_size:
            sampled = bin_data.sample(n=min_bin_size, random_state=42)
        else:
            sampled = bin_data
        resampled_dfs.append(sampled)
    
    resampled_df = pd.concat(resampled_dfs, ignore_index=True)
    
    # Calculate CV of the resampled target
    cv = calculate_cv(resampled_df[target_col].values)
    logger.info(f"Dynamic binning resampling complete. Resulting CV: {cv:.4f}")
    
    return resampled_df, cv

def fallback_resample(df: pd.DataFrame, target_col: str, 
                      synthetic_ratio: float = 0.30) -> Tuple[pd.DataFrame, float, Dict[str, Any]]:
    """
    Fallback resampling using SMOTE for regression when stratified binning fails.
    Logs synthetic data percentage and resulting CV.
    """
    logger.warning(f"Fallback resampling triggered for target: {target_col} using SMOTE")
    
    # Prepare features (exclude target and metadata)
    feature_cols = [col for col in df.columns if col != target_col and col != 'bin_id']
    X = df[feature_cols].values
    y = df[target_col].values
    
    # Calculate original size
    original_size = len(df)
    
    # Determine target size for SMOTE to keep synthetic <= 30%
    # If we add k synthetic samples, total = original + k
    # We want k / (original + k) <= synthetic_ratio
    # k <= synthetic_ratio * (original + k) => k * (1 - synthetic_ratio) <= synthetic_ratio * original
    # k <= (synthetic_ratio * original) / (1 - synthetic_ratio)
    max_synthetic = int((synthetic_ratio * original_size) / (1 - synthetic_ratio))
    
    # SMOTE for regression (requires continuous target handling)
    # Since sklearn's SMOTE is for classification, we use a regression-compatible approach
    # We will oversample by interpolating between neighbors
    # For simplicity in this context, we'll use a nearest-neighbor interpolation method
    # to generate synthetic points that respect the regression nature
    
    # Calculate number of synthetic samples to add
    n_synthetic = max_synthetic
    
    # Simple nearest-neighbor interpolation for regression SMOTE
    synthetic_indices = np.random.choice(original_size, size=n_synthetic, replace=True)
    neighbor_indices = np.random.choice(original_size, size=n_synthetic, replace=True)
    
    # Generate synthetic features and targets
    alpha = np.random.uniform(0, 1, size=n_synthetic)
    X_synthetic = X[synthetic_indices] + alpha.reshape(-1, 1) * (X[neighbor_indices] - X[synthetic_indices])
    y_synthetic = y[synthetic_indices] + alpha * (y[neighbor_indices] - y[synthetic_indices])
    
    # Create synthetic dataframe
    synthetic_df = df.iloc[synthetic_indices].copy()
    for i, col in enumerate(feature_cols):
        synthetic_df[col] = X_synthetic[:, i]
    synthetic_df[target_col] = y_synthetic
    synthetic_df['is_synthetic'] = True
    
    # Add is_synthetic flag to original data
    df['is_synthetic'] = False
    
    # Combine
    resampled_df = pd.concat([df, synthetic_df], ignore_index=True)
    
    # Calculate metrics
    synthetic_count = len(synthetic_df)
    total_count = len(resampled_df)
    synthetic_percentage = (synthetic_count / total_count) * 100
    
    # Calculate CV of combined dataset
    cv = calculate_cv(resampled_df[target_col].values)
    
    # Calculate CV of real data subset
    real_data_cv = calculate_cv(df[target_col].values)
    
    log_entry = {
        'target': target_col,
        'method': 'SMOTE_fallback',
        'original_size': original_size,
        'synthetic_added': synthetic_count,
        'total_size': total_count,
        'synthetic_percentage': synthetic_percentage,
        'combined_cv': cv,
        'real_data_cv': real_data_cv,
        'compliance': {
            'synthetic_le_30': synthetic_percentage <= 30.0,
            'combined_cv_le_030': cv <= COMBINED_CV_MAX,
            'real_data_cv_le_010': real_data_cv <= REAL_DATA_CV_MAX
        }
    }
    
    logger.info(f"SMOTE fallback complete for {target_col}: "
               f"Added {synthetic_count} synthetic samples ({synthetic_percentage:.2f}%). "
               f"Combined CV: {cv:.4f}, Real CV: {real_data_cv:.4f}")
    
    return resampled_df, cv, log_entry

def run_resampling_pipeline():
    """Main pipeline to run resampling and log results."""
    ensure_directories()
    
    # Load data
    df = load_processed_data()
    
    # Identify target columns (assumed to be columns ending with specific pattern or known targets)
    # For this implementation, we assume target columns are identified by the imbalance analysis
    # We'll look for common target property names or use a heuristic
    target_columns = [col for col in df.columns if col not in ['composition', 'is_synthetic'] and 
                     df[col].dtype in ['float64', 'int64'] and len(df[col].unique()) > 10]
    
    if not target_columns:
        logger.error("No target columns found for resampling")
        return
    
    logger.info(f"Found target columns for resampling: {target_columns}")
    
    all_log_entries = []
    results_by_target = {}
    
    for target in target_columns:
        logger.info(f"Processing target: {target}")
        
        # Try dynamic binning first
        try:
            resampled_df, cv = dynamic_binning_resample(df, target, num_bins=10)
            
            # Check if real data CV is acceptable
            real_data_cv = calculate_cv(df[target].values)
            
            if cv <= COMBINED_CV_MAX and real_data_cv <= REAL_DATA_CV_MAX:
                logger.info(f"Dynamic binning successful for {target}. CV: {cv:.4f}")
                log_entry = {
                    'target': target,
                    'method': 'dynamic_binning',
                    'original_size': len(df),
                    'resampled_size': len(resampled_df),
                    'synthetic_added': 0,
                    'synthetic_percentage': 0.0,
                    'combined_cv': cv,
                    'real_data_cv': real_data_cv,
                    'compliance': {
                        'synthetic_le_30': True,
                        'combined_cv_le_030': cv <= COMBINED_CV_MAX,
                        'real_data_cv_le_010': real_data_cv <= REAL_DATA_CV_MAX
                    }
                }
                results_by_target[target] = resampled_df
                all_log_entries.append(log_entry)
            else:
                # Fall back to SMOTE
                logger.warning(f"Dynamic binning CV {cv:.4f} exceeds threshold or real data CV {real_data_cv:.4f} exceeds threshold. Falling back to SMOTE.")
                resampled_df, cv, log_entry = fallback_resample(df, target)
                results_by_target[target] = resampled_df
                all_log_entries.append(log_entry)
                
        except Exception as e:
            logger.error(f"Error in dynamic binning for {target}: {e}. Attempting SMOTE fallback.")
            try:
                resampled_df, cv, log_entry = fallback_resample(df, target)
                results_by_target[target] = resampled_df
                all_log_entries.append(log_entry)
            except Exception as fallback_error:
                logger.critical(f"SMOTE fallback also failed for {target}: {fallback_error}")
                continue
    
    # Write resampling log
    if all_log_entries:
        with open(RESAMPLING_LOG_PATH, 'w') as f:
            json.dump(all_log_entries, f, indent=2)
        logger.info(f"Resampling log written to {RESAMPLING_LOG_PATH}")
        
        # Log summary for compliance check
        for entry in all_log_entries:
            if not entry['compliance']['synthetic_le_30']:
                logger.warning(f"COMPLIANCE VIOLATION: Synthetic data exceeds 30% for {entry['target']}: {entry['synthetic_percentage']:.2f}%")
            if not entry['compliance']['combined_cv_le_030']:
                logger.warning(f"COMPLIANCE VIOLATION: Combined CV exceeds 0.30 for {entry['target']}: {entry['combined_cv']:.4f}")
            if not entry['compliance']['real_data_cv_le_010']:
                logger.warning(f"COMPLIANCE VIOLATION: Real data CV exceeds 0.10 for {entry['target']}: {entry['real_data_cv']:.4f}")
    else:
        logger.warning("No resampling operations completed successfully.")

def main():
    """Entry point for resampling script."""
    logger.info("Starting resampling pipeline...")
    run_resampling_pipeline()
    logger.info("Resampling pipeline completed.")

if __name__ == "__main__":
    main()