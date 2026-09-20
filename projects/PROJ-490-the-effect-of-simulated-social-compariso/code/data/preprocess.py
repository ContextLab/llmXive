import os
import logging
from pathlib import Path
from typing import Optional, Tuple, Union
import pandas as pd
import numpy as np

from utils.logger import get_logger, log_execution_start, log_execution_end
from data.config import get_config

# Ensure logs directory exists
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

def calculate_missing_ratio(df: pd.DataFrame, column: str) -> float:
    """
    Calculate the ratio of missing values for a specific column.
    
    Args:
        df: Input DataFrame
        column: Column name to check
        
    Returns:
        Float ratio of missing values (0.0 to 1.0)
    """
    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found in DataFrame")
    
    total = len(df)
    if total == 0:
        return 0.0
    
    missing = df[column].isna().sum()
    return missing / total

def preprocess_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Preprocess the dataset according to T017 requirements.
    
    1. Normalize binary variables (specifically avatar_condition to 0/1).
    2. Compute change scores (post_self_esteem - pre_self_esteem) for 
       in-memory logging/diagnostics ONLY.
    3. DO NOT persist change scores to disk.
    4. Log a warning that change scores are for descriptive use only.
    
    CRITICAL: The primary model (ANCOVA) must use post_self_esteem as outcome 
    and pre_self_esteem as covariate to avoid mathematical coupling.
    
    Args:
        df: Input DataFrame containing raw or imputed data
        
    Returns:
        Tuple of (processed_df, diagnostics_df)
        - processed_df: DataFrame with normalized variables, ready for analysis
        - diagnostics_df: DataFrame containing only change scores for logging (not saved)
    """
    logger = get_logger(__name__)
    log_execution_start(logger, "preprocess_data")
    
    # Create a copy to avoid modifying the original
    processed_df = df.copy()
    
    # 1. Normalize binary variables (avatar_condition to 0/1)
    if 'avatar_condition' in processed_df.columns:
        # Convert to numeric first to handle potential string representations
        processed_df['avatar_condition'] = pd.to_numeric(
            processed_df['avatar_condition'], 
            errors='coerce'
        )
        
        # Ensure it's binary (0 or 1)
        unique_vals = processed_df['avatar_condition'].dropna().unique()
        if len(unique_vals) == 0:
            logger.warning("avatar_condition is entirely NaN. Cannot normalize.")
        elif set(unique_vals) == {0, 1}:
            logger.info("avatar_condition is already normalized to 0/1.")
        elif set(unique_vals) == {0.0, 1.0}:
            logger.info("avatar_condition is already normalized to 0.0/1.0.")
        elif set(unique_vals) <= {0, 1} and len(unique_vals) > 0:
            # Already binary, ensure integer type for consistency
            processed_df['avatar_condition'] = processed_df['avatar_condition'].astype(int)
            logger.info("avatar_condition normalized to binary integers (0/1).")
        else:
            # Attempt to map common binary representations to 0/1
            # e.g., ['neutral', 'idealized'] -> [0, 1]
            # e.g., [False, True] -> [0, 1]
            # e.g., [1, 2] -> [0, 1] (shifted)
            
            if len(unique_vals) == 2:
                sorted_vals = sorted(unique_vals)
                mapping = {sorted_vals[0]: 0, sorted_vals[1]: 1}
                processed_df['avatar_condition'] = processed_df['avatar_condition'].map(mapping)
                logger.info(f"avatar_condition mapped from {list(unique_vals)} to [0, 1].")
            else:
                logger.error(f"avatar_condition has non-binary values: {unique_vals}. Cannot normalize automatically.")
                raise ValueError(f"avatar_condition contains non-binary values: {unique_vals}")
    
    # 2. Compute change scores for in-memory logging/diagnostics ONLY
    diagnostics_df = pd.DataFrame()
    
    if 'post_self_esteem' in processed_df.columns and 'pre_self_esteem' in processed_df.columns:
        # Calculate change score
        change_scores = processed_df['post_self_esteem'] - processed_df['pre_self_esteem']
        diagnostics_df['change_score'] = change_scores
        
        # Log descriptive statistics for change scores (in-memory only)
        logger.warning(
            "Change scores (post - pre) computed for descriptive/diagnostic purposes ONLY. "
            "These are NOT used in the primary ANCOVA model to avoid mathematical coupling. "
            "DO NOT persist change scores to disk."
        )
        
        # Log summary stats
        mean_change = change_scores.mean()
        std_change = change_scores.std()
        logger.info(f"Change Score Diagnostics: Mean={mean_change:.4f}, Std={std_change:.4f}, N={len(change_scores)}")
    else:
        logger.warning("Cannot compute change scores: missing 'post_self_esteem' or 'pre_self_esteem' columns.")
    
    log_execution_end(logger, "preprocess_data")
    
    return processed_df, diagnostics_df

def run_preprocess() -> None:
    """
    Main entry point for the preprocessing step (T017).
    
    Loads imputed data from data/processed/imputed_data.csv,
    performs normalization and change score calculation,
    and saves the processed data to data/processed/preprocessed_data.csv.
    
    Change scores are computed but NOT saved to disk.
    """
    logger = get_logger(__name__)
    log_execution_start(logger, "run_preprocess")
    
    config = get_config()
    raw_data_path = Path(config.get('paths', {}).get('imputed_data', 'data/processed/imputed_data.csv'))
    output_path = Path(config.get('paths', {}).get('preprocessed_data', 'data/processed/preprocessed_data.csv'))
    
    if not raw_data_path.exists():
        raise FileNotFoundError(f"Input file not found: {raw_data_path}")
    
    logger.info(f"Loading data from: {raw_data_path}")
    df = pd.read_csv(raw_data_path)
    
    logger.info(f"Loaded {len(df)} rows, {len(df.columns)} columns")
    logger.info(f"Columns: {list(df.columns)}")
    
    # Perform preprocessing
    processed_df, diagnostics_df = preprocess_data(df)
    
    # Save processed data (excluding change scores)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    processed_df.to_csv(output_path, index=False)
    logger.info(f"Saved processed data to: {output_path}")
    
    # Log that change scores were NOT saved
    if not diagnostics_df.empty:
        logger.info("Change scores computed for diagnostics but NOT saved to disk (per T017 requirements).")
    
    log_execution_end(logger, "run_preprocess")

if __name__ == "__main__":
    run_preprocess()