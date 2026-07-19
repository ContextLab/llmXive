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
    logger.info("Applying log transformation to root metrics...")
    df = df.copy()
    
    for col in columns:
        if col not in df.columns:
            logger.warning(f"Column {col} not found for log transformation.")
            continue
        
        # Check for non-positive values before transformation
        non_positive = (df[col] <= 0).sum()
        if non_positive > 0:
            logger.warning(f"LOG TRANSFORM: Found {non_positive} non-positive values in {col}. Adding epsilon=1e-6.")
            df[col] = df[col].replace(0, 1e-6)
            # If negative, we shift by adding the absolute min + epsilon to ensure positivity
            min_val = df[col].min()
            if min_val < 0:
                shift = abs(min_val) + 1e-6
                df[col] = df[col] + shift
                logger.info(f"LOG TRANSFORM: Shifted {col} by {shift:.6f} to handle negative values.")
        
        # Apply log1p (log(1+x)) which is numerically stable for small x
        df[col] = np.log1p(df[col])
        logger.info(f"LOG TRANSFORM: Completed transformation for {col}.")
    
    return df

def apply_zscore_normalization(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    """
    Apply Z-score normalization (global) to specified columns.
    Calculates mean and std on the provided dataframe (assumed to be the filtered set).
    """
    logger.info("Applying Z-score normalization to nutrients...")
    df = df.copy()
    
    for col in columns:
        if col not in df.columns:
            logger.warning(f"Column {col} not found for z-score normalization.")
            continue
        
        # Only process if column has numeric data
        if not np.issubdtype(df[col].dtype, np.number):
            logger.warning(f"Column {col} is not numeric. Skipping z-score normalization.")
            continue

        mean_val = df[col].mean()
        std_val = df[col].std()
        
        if std_val == 0 or pd.isna(std_val):
            logger.warning(f"Z-SCORE: Standard deviation is 0 or NaN for {col}. Skipping normalization.")
            continue
        
        df[col] = (df[col] - mean_val) / std_val
        logger.info(f"Z-SCORE: Normalized {col} (mean={mean_val:.4f}, std={std_val:.4f}).")
    
    return df

def apply_knn_imputation(df: pd.DataFrame, columns: List[str], k: int = 5) -> pd.DataFrame:
    """
    Apply KNN imputation (k=5, Euclidean) to specified numeric columns.
    Note: Per spec deviation FR-003, KNN imputation is excluded for missing nutrients.
    This function remains for root metrics if needed, but should not be called on nutrient columns
    in the main pipeline for this project.
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
    Main execution for preprocessing pipeline (T016).
    
    Prerequisites:
    - T014: P/N columns must be verified.
    - T015: Rows with missing P/N and invalid data sources must be excluded.
    
    Logic:
    1. Load data from data/processed/merged_root_soil.csv (output of T015).
    2. Apply log transformation to root metrics (root_length, branching_density, surface_area).
    3. If p_n_available (checked via column presence), apply Z-score normalization to nutrients.
    4. Save output to data/processed/preprocessed_data.csv.
    """
    logger.info("Starting preprocessing pipeline (T016)...")
    
    try:
        input_path = Path("data/processed/merged_root_soil.csv")
        if not input_path.exists():
            raise FileNotFoundError(f"Input file {input_path} not found. Run data_ingestion.py (T015) first.")
        
        df = pd.read_csv(input_path)
        logger.info(f"Loaded {len(df)} rows from {input_path}")
        
        # Define columns for transformation
        root_metrics = ['root_length', 'branching_density', 'surface_area']
        nutrients = ['phosphorus', 'nitrogen']
        
        # 1. Log transformation for root metrics
        # Filter out rows where root metrics are missing before transform if necessary, 
        # but log1p handles 0. We assume T015 handled critical exclusions.
        df = apply_log_transformation(df, root_metrics)
        
        # 2. Z-score normalization for nutrients
        # Constraint: Normalize ONLY after T015 excluded rows with missing nutrients.
        # Check if nutrient columns exist (should be true per T014)
        p_n_available = all(col in df.columns for col in nutrients)
        
        if p_n_available:
            # Check for any remaining NaNs in nutrients (should be 0 per T015 constraint)
            na_counts = df[nutrients].isna().sum()
            if na_counts.sum() > 0:
                logger.warning(f"Found {na_counts.sum()} missing nutrient values. Skipping Z-score for affected rows.")
                # Drop rows with missing nutrients for normalization step to avoid NaN propagation
                # Or impute if allowed (but spec says exclude). We drop for normalization calculation.
                df_clean_nutrients = df.dropna(subset=nutrients)
                if len(df_clean_nutrients) == 0:
                    raise ValueError("No valid rows left for nutrient normalization after dropping NaNs.")
                
                # Calculate stats on clean rows, apply to all (or just clean rows?)
                # Z-score is global: calculate on the valid set, apply to the valid set.
                # We will normalize the valid rows.
                df[nutrients] = df[nutrients].where(df[nutrients].notna(), np.nan) # Ensure NaNs stay NaN
                
                # Normalize only the non-NaN rows
                for col in nutrients:
                    if col in df.columns and df[col].notna().any():
                        mean_val = df[col].mean()
                        std_val = df[col].std()
                        if std_val > 0 and not pd.isna(std_val):
                            df[col] = (df[col] - mean_val) / std_val
                            logger.info(f"Z-SCORE: Normalized {col} (mean={mean_val:.4f}, std={std_val:.4f}).")
            else:
                df = apply_zscore_normalization(df, nutrients)
        else:
            logger.warning("P/N columns not available. Skipping nutrient normalization.")
        
        # 3. KNN Imputation is explicitly excluded for nutrients per FR-003 deviation.
        # We do NOT call apply_knn_imputation here for nutrients.
        # If root metrics have missing values, we could impute, but T015 should have cleaned data.
        # We skip KNN for this task to adhere to "missing nutrients are excluded" rule strictly.
        
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