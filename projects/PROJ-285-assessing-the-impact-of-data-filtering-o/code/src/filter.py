"""
Filtering module for gravitational lens detection analysis.
Implements threshold-based filtering on the SLFC dataset.
"""
import os
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Tuple, List, Optional, Dict, Any

from .logging_config import get_logger, ThresholdFilterError
from .error_utils import validate_data_frame_columns, validate_not_null

# Configure logger
logger = get_logger(__name__)

# Constants for thresholds
SNR_MIN = 5
SNR_MAX = 20  # Exclusive in range, so 20 is included
SNR_STEP = 1
MORPH_MIN = 0.3
MORPH_MAX = 0.95  # Exclusive in arange, so 0.9 is the last value
MORPH_STEP = 0.1
MISSING_THRESHOLD = -999  # Value used to mark missing data

def generate_threshold_grid() -> Tuple[List[int], List[float]]:
    """
    Generate the grid of SNR and Morphology thresholds.
    
    Returns:
        Tuple of (snr_thresholds, morph_thresholds)
    """
    snr_thresholds = list(range(SNR_MIN, SNR_MAX + SNR_STEP, SNR_STEP))
    # Ensure we cover the range up to 0.9 with step 0.1
    # np.arange(0.3, 0.95, 0.1) generates: 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9
    morph_thresholds = np.arange(MORPH_MIN, MORPH_MAX, MORPH_STEP).tolist()
    
    logger.info(f"Generated SNR grid: {snr_thresholds}")
    logger.info(f"Generated Morph grid: {morph_thresholds}")
    
    return snr_thresholds, morph_thresholds

def filter_by_thresholds(
    df: pd.DataFrame,
    snr_col: str = 'snr',
    morph_col: str = 'morph'
) -> pd.DataFrame:
    """
    Filter the dataset based on SNR and Morphology thresholds.
    
    This function iterates over all combinations of SNR and Morphology thresholds
    defined in the grid and counts the number of detections for each pair.
    
    Args:
        df: Input DataFrame containing the SLFC dataset
        snr_col: Column name for SNR values
        morph_col: Column name for Morphology values
        
    Returns:
        DataFrame containing detection counts for each threshold pair
    """
    # Validate input
    validate_not_null(df, "Input DataFrame")
    validate_data_frame_columns(df, [snr_col, morph_col])
    
    # Handle missing values by filtering them out first
    df_clean = df.dropna(subset=[snr_col, morph_col])
    logger.info(f"Filtered {len(df) - len(df_clean)} rows with missing values")
    
    # Generate threshold grid
    snr_thresholds, morph_thresholds = generate_threshold_grid()
    
    # Initialize results list
    results = []
    
    total_pairs = len(snr_thresholds) * len(morph_thresholds)
    current_pair = 0
    
    for snr_thresh in snr_thresholds:
        for morph_thresh in morph_thresholds:
            current_pair += 1
            
            # Apply filtering
            mask = (df_clean[snr_col] >= snr_thresh) & (df_clean[morph_col] >= morph_thresh)
            count = mask.sum()
            
            results.append({
                'snr_threshold': snr_thresh,
                'morph_threshold': morph_thresh,
                'detection_count': int(count)
            })
            
            # Log progress every 10%
            if current_pair % max(1, total_pairs // 10) == 0:
                logger.info(f"Processed {current_pair}/{total_pairs} threshold pairs")
    
    logger.info(f"Completed filtering for {total_pairs} threshold pairs")
    
    return pd.DataFrame(results)

def main():
    """
    Main entry point for running the filter_by_thresholds analysis.
    Loads the SLFC dataset, applies threshold filtering, and saves results.
    """
    try:
        logger.info("Starting threshold filtering analysis")
        
        # Load the SLFC dataset
        # Assuming the dataset is available in the data/processed directory
        # after T005 has processed it
        data_path = Path("data/processed/slfc_processed.parquet")
        
        if not data_path.exists():
            # Fallback to CSV if parquet doesn't exist
            data_path = Path("data/processed/slfc_processed.csv")
            
        if not data_path.exists():
            # Try to load from raw if processed doesn't exist
            data_path = Path("data/raw/slfc_dataset.parquet")
            if not data_path.exists():
                data_path = Path("data/raw/slfc_dataset.csv")
        
        if not data_path.exists():
            raise FileNotFoundError(
                f"Could not find SLFC dataset at expected paths: "
                f"data/processed/slfc_processed.*, data/raw/slfc_dataset.*"
            )
        
        logger.info(f"Loading dataset from {data_path}")
        
        # Load the data
        if data_path.suffix == '.parquet':
            df = pd.read_parquet(data_path)
        else:
            df = pd.read_csv(data_path)
        
        logger.info(f"Loaded {len(df)} rows from dataset")
        
        # Apply filtering
        result_df = filter_by_thresholds(df)
        
        # Save results
        output_path = Path("data/processed/detection_matrix.csv")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        result_df.to_csv(output_path, index=False)
        
        logger.info(f"Saved detection matrix to {output_path}")
        logger.info(f"Detection matrix shape: {result_df.shape}")
        logger.info(f"Total detections across all thresholds: {result_df['detection_count'].sum()}")
        
        return result_df
        
    except Exception as e:
        logger.error(f"Error in main filtering process: {e}", exc_info=True)
        raise ThresholdFilterError(f"Failed to execute threshold filtering: {e}") from e

if __name__ == "__main__":
    main()
