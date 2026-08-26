import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, Optional, Dict, Any
from utils.logging import get_logger, log_info, log_warning, log_error

logger = get_logger(__name__)

def normalize_features(df: pd.DataFrame, method: str = "zscore") -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Normalizes tabular features using z-score or min-max scaling.
    Handles missing values via mean imputation.
    
    Args:
        df: Input DataFrame with tabular features. Must contain 'dataset_id' column if multiple datasets are present.
        method: 'zscore' (standardization) or 'minmax' (0-1 scaling).
    
    Returns:
        Tuple of (normalized DataFrame, metadata dict containing mean/std or min/max for each feature).
    """
    if df.empty:
        log_warning("Input DataFrame is empty. Returning empty DataFrame.")
        return df, {}

    # Identify numeric columns to normalize
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # Remove 'dataset_id' if present (ensure it's not treated as numeric)
    if 'dataset_id' in numeric_cols:
        numeric_cols.remove('dataset_id')
    
    if not numeric_cols:
        log_warning("No numeric columns found to normalize.")
        return df, {}

    metadata = {}
    normalized_df = df.copy()

    for col in numeric_cols:
        col_data = normalized_df[col].copy()
        
        # Handle missing values: Mean Imputation
        mean_val = col_data.mean()
        if pd.isna(mean_val):
            mean_val = 0.0
            log_warning(f"Mean for {col} is NaN, using 0.0 for imputation.")
        
        # Fill NaNs with mean
        col_data = col_data.fillna(mean_val)
        
        if method == "zscore":
            std_val = col_data.std()
            if std_val == 0 or pd.isna(std_val):
                # If variance is zero, keep the mean (or 0 if mean was 0)
                # We still record the mean/std for consistency
                std_val = 1.0 # Prevent division by zero, effectively keeping mean
                log_warning(f"Standard deviation for {col} is 0. Keeping values as mean.")
            
            normalized_col = (col_data - mean_val) / std_val
            metadata[col] = {"mean": float(mean_val), "std": float(std_val), "method": "zscore"}
        
        elif method == "minmax":
            min_val = col_data.min()
            max_val = col_data.max()
            range_val = max_val - min_val
            if range_val == 0:
                range_val = 1.0
                log_warning(f"Range for {col} is 0. Keeping values as 0.")
            
            normalized_col = (col_data - min_val) / range_val
            metadata[col] = {"min": float(min_val), "max": float(max_val), "method": "minmax"}
        else:
            raise ValueError(f"Unsupported normalization method: {method}")
        
        normalized_df[col] = normalized_col

    return normalized_df, metadata

def save_normalization_metadata(metadata: Dict[str, Any], path: Path):
    """
    Saves normalization parameters to a JSON file for later reuse (e.g., by T019d).
    """
    import json
    with open(path, 'w') as f:
        json.dump(metadata, f, indent=2)
    log_info(f"Saved normalization metadata to {path}")

def load_normalization_metadata(path: Path) -> Dict[str, Any]:
    """
    Loads normalization parameters from a JSON file.
    """
    import json
    with open(path, 'r') as f:
        return json.load(f)