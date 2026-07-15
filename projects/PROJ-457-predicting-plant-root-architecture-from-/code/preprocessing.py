import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import math

import pandas as pd
import numpy as np
from sklearn.impute import KNNImputer

# Import config utilities
try:
    from config import get_config, setup_logging
except ImportError:
    import yaml
    def get_config():
        return {"SEED": 42, "DATA_PATH": "data"}
    def setup_logging():
        logging.basicConfig(level=logging.INFO)
        return logging.getLogger(__name__)

logger = setup_logging()

def apply_log_transformation(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    """
    Apply log transformation to specified columns.
    Handles zeros and negatives by adding a small epsilon or logging exclusion.
    """
    logger.info("Applying log transformation...")
    df = df.copy()
    
    for col in columns:
        if col not in df.columns:
            logger.warning(f"Column {col} not found for log transformation.")
            continue
        
        non_positive = (df[col] <= 0).sum()
        if non_positive > 0:
            logger.warning(f"LOG TRANSFORM: Found {non_positive} non-positive values in {col}. Adding epsilon=1e-6.")
            df[col] = df[col].replace(0, 1e-6)
            # If negative, we might need to shift, but for root metrics usually > 0.
            # Assuming we just add epsilon to handle 0.
        
        df[col] = np.log1p(df[col])
        logger.info(f"LOG TRANSFORM: Completed transformation for {col}.")
    
    return df

def apply_zscore_normalization(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    """
    Apply Z-score normalization (global) to specified columns.
    """
    logger.info("Applying Z-score normalization...")
    df = df.copy()
    
    for col in columns:
        if col not in df.columns:
            logger.warning(f"Column {col} not found for z-score normalization.")
            continue
        
        mean_val = df[col].mean()
        std_val = df[col].std()
        
        if std_val == 0:
            logger.warning(f"Z-SCORE: Standard deviation is 0 for {col}. Skipping normalization.")
            continue
        
        df[col] = (df[col] - mean_val) / std_val
        logger.info(f"Z-SCORE: Normalized {col} (mean={mean_val:.4f}, std={std_val:.4f}).")
    
    return df

def apply_knn_imputation(df: pd.DataFrame, columns: List[str], k: int = 5) -> pd.DataFrame:
    """
    Apply KNN imputation (k=5, Euclidean) to specified numeric columns.
    """
    logger.info(f"Applying KNN imputation (k={k})...")
    df = df.copy()
    
    # Select only numeric columns that exist
    numeric_cols = [c for c in columns if c in df.columns and np.issubdtype(df[c].dtype, np.number)]
    
    if not numeric_cols:
        logger.warning("No numeric columns found for KNN imputation.")
        return df
    
    # Check for missing values
    missing_counts = df[numeric_cols].isna().sum()
    total_missing = missing_counts.sum()
    
    if total_missing == 0:
        logger.info("No missing values found for KNN imputation.")
        return df
    
    logger.info(f"Found {total_missing} missing values across {len(numeric_cols)} columns.")
    
    imputer = KNNImputer(n_neighbors=k, weights='distance')
    imputed_values = imputer.fit_transform(df[numeric_cols])
    
    df[numeric_cols] = imputed_values
    
    logger.info("KNN imputation complete.")
    return df

def main():
    """
    Main execution for preprocessing pipeline.
    """
    logger.info("Starting preprocessing pipeline (T019: Logging integration)...")
    
    try:
        input_path = Path("data/processed/merged_root_soil.csv")
        if not input_path.exists():
            raise FileNotFoundError(f"Input file {input_path} not found. Run data_ingestion.py first.")
        
        df = pd.read_csv(input_path)
        
        # Define columns for transformation
        root_metrics = ['root_length', 'branching_density', 'surface_area']
        nutrients = ['phosphorus', 'nitrogen']
        
        # 1. Log transformation for root metrics
        df = apply_log_transformation(df, root_metrics)
        
        # 2. Z-score normalization for nutrients
        df = apply_zscore_normalization(df, nutrients)
        
        # 3. KNN Imputation for any remaining missing values
        df = apply_knn_imputation(df, root_metrics + nutrients)
        
        # Save output
        output_path = Path("data/processed/preprocessed_data.csv")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        logger.info(f"Preprocessing complete. Output saved to {output_path}")
        
    except Exception as e:
        logger.error(f"Preprocessing pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()