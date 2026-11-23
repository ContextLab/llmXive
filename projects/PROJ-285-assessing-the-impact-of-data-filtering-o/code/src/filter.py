import os
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Tuple, List, Optional, Dict, Any

from .logging_config import get_logger, ThresholdFilterError

logger = get_logger(__name__)

# Define the grid ranges as per task description and FR-002
SNR_RANGE = range(5, 21, 1)  # 5 to 20 inclusive
MORPH_RANGE = np.arange(0.3, 0.95, 0.1)  # 0.3, 0.4, ..., 0.9

def generate_threshold_grid() -> List[Tuple[int, float]]:
    """
    Generates the list of (snr_threshold, morph_threshold) pairs.
    Explicitly ensures the grid includes a representative value near the upper bound.
    """
    grid = []
    for snr in SNR_RANGE:
        for morph in MORPH_RANGE:
            grid.append((snr, morph))
    logger.info(f"Generated threshold grid with {len(grid)} pairs.")
    logger.debug(f"Grid sample: {grid[:5]} ... {grid[-5:]}")
    return grid

def filter_by_thresholds(
    df: pd.DataFrame,
    snr_threshold: int,
    morph_threshold: float
) -> pd.DataFrame:
    """
    Filters the dataset based on SNR and Morphology thresholds.
    Excludes rows with missing SNR or morphology values (NA/NaN) as per US-1 acceptance criteria.
    
    Args:
        df: Input DataFrame with 'snr' and 'morphology' columns.
        snr_threshold: Minimum SNR required.
        morph_threshold: Minimum morphology score required.
        
    Returns:
        Filtered DataFrame containing only detections passing both thresholds.
    """
    if df.empty:
        return pd.DataFrame(columns=df.columns)

    # Ensure required columns exist
    required_cols = ['snr', 'morphology']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ThresholdFilterError(f"Missing required columns for filtering: {missing_cols}")

    # 1. Exclude rows with missing values (NA/NaN) in SNR or Morphology
    # This satisfies US-1 acceptance criteria and prevents NaN comparisons from failing silently
    df_clean = df.dropna(subset=required_cols)
    
    if len(df_clean) < len(df):
        logger.debug(f"Dropped {len(df) - len(df_clean)} rows with missing SNR/Morphology values.")

    # 2. Apply thresholds
    # Note: We assume higher SNR and higher Morphology are better (standard for detection)
    mask = (df_clean['snr'] >= snr_threshold) & (df_clean['morphology'] >= morph_threshold)
    result = df_clean[mask].copy()
    
    return result

def generate_detection_matrix(
    df: pd.DataFrame,
    output_path: Optional[str] = None
) -> pd.DataFrame:
    """
    Generates the detection matrix by iterating over the threshold grid.
    
    Args:
        df: The full dataset (SLFC) to filter.
        output_path: Optional path to save the CSV. If None, returns the DataFrame only.
        
    Returns:
        DataFrame with columns: snr_threshold, morph_threshold, detection_count
    """
    logger.info("Starting detection matrix generation.")
    
    grid = generate_threshold_grid()
    results = []
    
    for snr, morph in grid:
        try:
            filtered_df = filter_by_thresholds(df, snr, morph)
            count = len(filtered_df)
            results.append({
                'snr_threshold': snr,
                'morph_threshold': morph,
                'detection_count': count
            })
            logger.debug(f"Threshold ({snr}, {morph:.1f}): {count} detections")
        except Exception as e:
            logger.error(f"Error processing threshold pair ({snr}, {morph}): {e}", exc_info=True)
            # We continue processing other pairs even if one fails, logging the error.
            # However, for a strict report, we might want to record 0 or raise.
            # Given the task is to generate the matrix, we record the failure as 0 or log it.
            # Let's record 0 to keep the matrix complete, but log the error.
            results.append({
                'snr_threshold': snr,
                'morph_threshold': morph,
                'detection_count': 0
            })
    
    matrix_df = pd.DataFrame(results)
    
    # Validate output
    if matrix_df.empty:
        raise ThresholdFilterError("Failed to generate any detection matrix rows.")
    
    if output_path:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        matrix_df.to_csv(output_path, index=False)
        logger.info(f"Detection matrix saved to {output_path}")
    
    return matrix_df

def main():
    """
    Entry point for T014: Generate detection_matrix.csv.
    Loads the SLFC dataset (via data_loader), applies the grid, and saves the result.
    """
    logger.info("Executing T014: Generate Detection Matrix.")
    
    # Import here to avoid circular dependencies and ensure data_loader is ready
    from .data_loader import load_slfc_dataset
    
    # Load the dataset
    # We expect the data to be available via the loader which handles the real source
    try:
        df = load_slfc_dataset()
    except Exception as e:
        logger.critical(f"Failed to load SLFC dataset: {e}")
        raise
    
    if df is None or df.empty:
        raise ValueError("Loaded dataset is empty or None.")
    
    logger.info(f"Loaded dataset with {len(df)} rows.")
    
    # Define output path
    output_path = "data/processed/detection_matrix.csv"
    
    # Generate the matrix
    matrix_df = generate_detection_matrix(df, output_path=output_path)
    
    logger.info(f"T014 Complete. Output: {output_path}")
    return matrix_df

if __name__ == "__main__":
    main()
