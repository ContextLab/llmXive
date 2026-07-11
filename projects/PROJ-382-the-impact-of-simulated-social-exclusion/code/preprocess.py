"""
Preprocessing module for the social exclusion impact analysis pipeline.

Handles:
- Missing value imputation (median vs exclusion)
- Pool splitting (Causal vs Associational)
- Data quality filtering
"""
import json
from pathlib import Path
from typing import Tuple, Dict, Any, Optional

import pandas as pd
import numpy as np
import logging

from logging_config import get_project_logger

logger = get_project_logger(__name__)


def handle_missing_values(
    df: pd.DataFrame,
    target_column: str,
    log_path: Path
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Handle missing values in a DataFrame column.
    
    Rules:
    - If NaN percentage < 5%: Impute with median (excluding 0s)
    - If NaN percentage >= 5%: Exclude rows with NaN
    - Structural zeros (0) are NEVER imputed
    
    Args:
        df: Input DataFrame
        target_column: Column to check for missing values
        log_path: Path to write imputation log
        
    Returns:
        Tuple of (cleaned DataFrame, imputation details dict)
    """
    if target_column not in df.columns:
        raise ValueError(f"Column '{target_column}' not found in DataFrame")
    
    total_rows = len(df)
    nan_count = df[target_column].isna().sum()
    nan_percentage = (nan_count / total_rows * 100) if total_rows > 0 else 0
    
    # Separate structural zeros from missing values
    df_copy = df.copy()
    
    # Identify structural zeros (0 values) - these should NOT be imputed
    structural_zeros_mask = (df_copy[target_column] == 0)
    missing_mask = df_copy[target_column].isna()
    
    imputation_details = {
        "column": target_column,
        "total_rows": int(total_rows),
        "nan_count": int(nan_count),
        "nan_percentage": float(nan_percentage),
        "structural_zeros_count": int(structural_zeros_mask.sum()),
        "action": "",
        "rows_excluded": 0,
        "rows_imputed": 0,
        "imputation_value": None
    }
    
    if nan_percentage < 5.0:
        # Median imputation (excluding 0s and NaNs)
        valid_values = df_copy.loc[
            ~structural_zeros_mask & ~missing_mask, 
            target_column
        ]
        
        if len(valid_values) > 0:
            median_val = valid_values.median()
            imputation_details["action"] = "median_imputation"
            imputation_details["imputation_value"] = float(median_val)
            
            # Only impute where missing (not where zero)
            df_copy.loc[missing_mask, target_column] = median_val
            imputation_details["rows_imputed"] = int(nan_count)
            logger.info(f"Imputed {nan_count} missing values in '{target_column}' with median {median_val:.2f}")
        else:
            # No valid values to compute median, treat as exclusion
            df_copy = df_copy[~missing_mask]
            imputation_details["action"] = "exclusion_no_valid_data"
            imputation_details["rows_excluded"] = int(nan_count)
            logger.warning(f"No valid non-zero values in '{target_column}' to compute median. Excluding {nan_count} rows.")
    else:
        # Exclude rows with missing values
        df_copy = df_copy[~missing_mask]
        imputation_details["action"] = "row_exclusion"
        imputation_details["rows_excluded"] = int(nan_count)
        logger.info(f"Excluded {nan_count} rows with missing values in '{target_column}' (NaN%: {nan_percentage:.2f}%)")
    
    # Ensure structural zeros are preserved (they should be untouched)
    if structural_zeros_mask.sum() > 0:
        preserved_zeros = df_copy.loc[structural_zeros_mask, target_column]
        if not all(preserved_zeros == 0):
            raise AssertionError("Structural zeros were modified!")
    
    # Write log
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, 'w') as f:
        json.dump(imputation_details, f, indent=2)
    
    return df_copy, imputation_details


def split_pools(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split data into Causal (RCT) and Associational pools.
    
    Causal pool: randomized = True
    Associational pool: randomized = False or unknown/missing
    
    Args:
        df: Input DataFrame with 'randomized' column
        
    Returns:
        Tuple of (causal_pool_df, associational_pool_df)
    """
    if 'randomized' not in df.columns:
        logger.warning("No 'randomized' column found. Treating all data as Associational pool.")
        return pd.DataFrame(), df.copy()
    
    causal_pool = df[df['randomized'] == True].copy()
    associational_pool = df[df['randomized'] != True].copy()
    
    logger.info(f"Split pools: Causal={len(causal_pool)}, Associational={len(associational_pool)}")
    
    return causal_pool, associational_pool


def filter_small_samples(
    df: pd.DataFrame,
    condition_column: str = 'condition',
    exclusion_value: int = 1,
    min_sample_size: int = 5,
    output_path: Optional[Path] = None
) -> pd.DataFrame:
    """
    Filter out datasets where the exclusion group sample size is too small.
    
    Args:
        df: Input DataFrame
        condition_column: Column name for condition
        exclusion_value: Value representing the exclusion condition (default: 1)
        min_sample_size: Minimum required sample size for exclusion group
        output_path: Optional path to write filtered dataset list
        
    Returns:
        Filtered DataFrame
    """
    if condition_column not in df.columns:
        logger.warning(f"Condition column '{condition_column}' not found. Returning original data.")
        return df
    
    # Count exclusion group size
    exclusion_count = (df[condition_column] == exclusion_value).sum()
    
    if exclusion_count < min_sample_size:
        logger.warning(f"Exclusion group size ({exclusion_count}) < {min_sample_size}. Filtering dataset.")
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump({"filtered": True, "reason": f"Exclusion group size {exclusion_count} < {min_sample_size}"}, f, indent=2)
        return pd.DataFrame() # Return empty DF to indicate filtering
    
    logger.info(f"Exclusion group size ({exclusion_count}) >= {min_sample_size}. Keeping dataset.")
    return df.copy()