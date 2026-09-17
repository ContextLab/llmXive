"""
Preprocessing pipeline for User Story 2: Calculate Alignment Deviation Score.

This module implements the deviation calculation logic (T025a) and provides
a script wrapper (T025b) to materialize the deviation dataset to disk.

Key Functions:
- validate_clip_scores: Validates presence of 'clip_score' column.
- normalize_and_calculate_deviation: Normalizes CLIP/Human scores and computes |CLIP - Human|.
- compute_deviation_batch: Orchestrates the full deviation calculation pipeline.
- main: Script entry point to save data/processed/deviation.csv.
"""
import os
import sys
import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
from scipy.stats import shapiro

# Project root imports
from config import get_paths, init_run
from utils.logging import setup_logging, get_logger
from utils.errors import DataSchemaError, create_missing_dataset_error

# Constants
TARGET_COLUMN = "deviation_score"
CLIP_COLUMN = "clip_score"
HUMAN_COLUMN = "human_rating"
OUTPUT_FILE = "data/processed/deviation.csv"
RAW_INPUT_FILE = "data/raw/pick-a-pic.parquet"
FEATURES_INPUT_FILE = "data/processed/features.csv"

# Initialize logger
logger = get_logger(__name__)

class HumanRatingResult:
    """Container for deviation calculation results."""
    def __init__(self, deviation_scores: List[float], excluded_count: int, reason: str = "success"):
        self.deviation_scores = deviation_scores
        self.excluded_count = excluded_count
        self.reason = reason

def validate_clip_scores(dataset: pd.DataFrame) -> pd.DataFrame:
    """
    Validates the presence of the 'clip_score' column in the dataset.
    
    Args:
        dataset: The input DataFrame (expected to contain pick-a-pic data).
        
    Returns:
        The same DataFrame if validation passes.
        
    Raises:
        DataSchemaError: If 'clip_score' column is missing.
    """
    if CLIP_COLUMN not in dataset.columns:
        error_msg = create_missing_dataset_error("pick-a-pic", CLIP_COLUMN)
        logger.error(error_msg)
        raise DataSchemaError(error_msg)
    
    logger.info(f"Validation passed: '{CLIP_COLUMN}' column found.")
    return dataset

def normalize_and_calculate_deviation(clip_scores: List[float], human_ratings: List[float]) -> List[float]:
    """
    Normalizes CLIP and Human scores and calculates absolute deviation |CLIP - Human|.
    
    Process:
    1. Check for Gaussian distribution using Shapiro-Wilk.
    2. If non-Gaussian (p < 0.05), apply Rank-based Inverse Normal Transformation (INT).
    3. If Gaussian, apply Z-score normalization.
    4. Calculate absolute difference.
    
    Args:
        clip_scores: List of raw CLIP scores.
        human_ratings: List of raw human ratings.
        
    Returns:
        List of deviation scores.
        
    Raises:
        ValueError: If inputs have zero variance after normalization.
    """
    if len(clip_scores) != len(human_ratings):
        raise ValueError("Input lists must have the same length.")
    
    if len(clip_scores) == 0:
        return []

    clip_arr = np.array(clip_scores)
    human_arr = np.array(human_ratings)

    # Helper for INT
    def apply_int(arr: np.ndarray) -> np.ndarray:
        # Rank-based inverse normal transformation
        # 1. Get ranks (1-based)
        ranks = np.argsort(np.argsort(arr)) + 1
        # 2. Normalize ranks to (0, 1) avoiding 0 and 1
        n = len(arr)
        normalized_ranks = (ranks - 0.5) / n
        # 3. Inverse CDF of standard normal
        return np.percentile(arr, normalized_ranks * 100) 
        # Note: A more standard INT implementation:
        # from scipy.stats import norm
        # return norm.ppf((ranks - 0.5) / n)
    
    # Standard INT implementation using norm.ppf
    from scipy.stats import norm
    def safe_int_transform(arr: np.ndarray) -> np.ndarray:
        if len(arr) == 0: return arr
        # Avoid duplicates for rank calculation if necessary, but argsort handles ties by index
        # Standard INT: rank -> (rank - 0.5) / n -> norm.ppf
        ranks = np.argsort(np.argsort(arr)) + 1
        u = (ranks - 0.5) / len(arr)
        # Clip to avoid inf
        u = np.clip(u, 1e-10, 1 - 1e-10)
        return norm.ppf(u)

    def safe_zscore(arr: np.ndarray) -> np.ndarray:
        mean = np.mean(arr)
        std = np.std(arr)
        if std == 0:
            raise ValueError(f"Zero variance detected in array with mean {mean}")
        return (arr - mean) / std

    # Shapiro-Wilk test
    # Note: Shapiro-Wilk has a limit (n <= 5000). If larger, we might skip or sample.
    # For robustness, if n > 5000, we assume non-Gaussian and apply INT.
    apply_shapiro = len(clip_arr) <= 5000
    is_gaussian = True
    
    if apply_shapiro:
        try:
            stat_clip, p_clip = shapiro(clip_arr)
            stat_human, p_human = shapiro(human_arr)
            if p_clip < 0.05 or p_human < 0.05:
                is_gaussian = False
                logger.debug("Shapiro-Wilk indicates non-Gaussian distribution. Applying INT.")
        except Exception as e:
            logger.warning(f"Shapiro-Wilk test failed ({e}). Defaulting to INT.")
            is_gaussian = False
    else:
        logger.debug("Sample size > 5000. Skipping Shapiro-Wilk. Applying INT.")
        is_gaussian = False

    # Normalize
    if is_gaussian:
        try:
            norm_clip = safe_zscore(clip_arr)
            norm_human = safe_zscore(human_arr)
        except ValueError as e:
            logger.error(f"Normalization failed: {e}")
            raise ValueError("Target not learnable: zero variance detected")
    else:
        # Apply INT to both
        norm_clip = safe_int_transform(clip_arr)
        norm_human = safe_int_transform(human_arr)

    # Calculate Deviation
    deviations = np.abs(norm_clip - norm_human)
    
    # Check for zero variance in the target
    if np.std(deviations) == 0:
        logger.error("Target variable has zero variance.")
        raise ValueError("Target not learnable: zero variance detected")

    return deviations.tolist()

def compute_deviation_batch(raw_df: pd.DataFrame, features_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """
    Orchestrates the deviation calculation pipeline.
    
    1. Validates raw data for 'clip_score' and 'human_rating'.
    2. Merges with features if provided (optional for T025b context, but good practice).
    3. Excludes rows with missing human ratings.
    4. Calculates deviation.
    5. Returns DataFrame with deviation scores.
    
    Args:
        raw_df: The raw pick-a-pic DataFrame.
        features_df: Optional features DataFrame to merge.
        
    Returns:
        DataFrame with 'deviation_score' column.
    """
    # Validate CLIP scores
    raw_df = validate_clip_scores(raw_df)
    
    # Check for human_rating (required for deviation)
    if HUMAN_COLUMN not in raw_df.columns:
        error_msg = create_missing_dataset_error("pick-a-pic", HUMAN_COLUMN)
        logger.error(error_msg)
        raise DataSchemaError(error_msg)
    
    # Initial row count
    total_rows = len(raw_df)
    
    # Exclude missing human ratings
    valid_mask = raw_df[HUMAN_COLUMN].notna() & raw_df[CLIP_COLUMN].notna()
    excluded_count = total_rows - valid_mask.sum()
    
    if excluded_count > 0:
        logger.info(f"Excluded {excluded_count} rows due to missing {CLIP_COLUMN} or {HUMAN_COLUMN}.")
    
    valid_df = raw_df[valid_mask].copy()
    
    if len(valid_df) == 0:
        raise ValueError("No valid rows remaining after excluding missing ratings.")

    # Extract lists
    clip_list = valid_df[CLIP_COLUMN].tolist()
    human_list = valid_df[HUMAN_COLUMN].tolist()
    
    # Calculate deviations
    deviations = normalize_and_calculate_deviation(clip_list, human_list)
    
    # Assign back to the valid dataframe
    valid_df[TARGET_COLUMN] = deviations
    
    # If features were provided, we might want to merge them back for the final output
    # However, T025b specifically asks for deviation.csv. We will keep it focused on the target.
    # If the downstream task needs features, they will load features.csv separately or this can be extended.
    # For now, we output the deviation scores aligned with the valid rows.
    
    logger.info(f"Deviation calculation complete. {len(valid_df)} rows processed.")
    return valid_df

def main():
    """
    Script entry point for T025b.
    Loads raw data, computes deviation, validates against contract, and saves to disk.
    """
    init_run()
    paths = get_paths()
    
    # Ensure output directory exists
    output_dir = os.path.dirname(paths.processed_dir / OUTPUT_FILE)
    os.makedirs(output_dir, exist_ok=True)
    
    logger.info(f"Starting T025b: Deviation Calculation.")
    logger.info(f"Input: {paths.raw_dir / RAW_INPUT_FILE}")
    logger.info(f"Output: {paths.processed_dir / OUTPUT_FILE}")
    
    try:
        # Load raw data
        logger.info("Loading raw dataset...")
        raw_df = pd.read_parquet(paths.raw_dir / RAW_INPUT_FILE)
        logger.info(f"Loaded {len(raw_df)} rows.")
        
        # Compute deviation
        logger.info("Computing deviation scores...")
        deviation_df = compute_deviation_batch(raw_df)
        
        # Basic schema validation (Contract check)
        # Expected columns: original columns + deviation_score
        required_cols = [CLIP_COLUMN, HUMAN_COLUMN, TARGET_COLUMN]
        missing_cols = [c for c in required_cols if c not in deviation_df.columns]
        if missing_cols:
            raise ValueError(f"Output missing required columns: {missing_cols}")
        
        # Save to disk
        output_path = paths.processed_dir / OUTPUT_FILE
        deviation_df.to_csv(output_path, index=False)
        logger.info(f"Saved deviation data to {output_path}")
        
        logger.info("T025b completed successfully.")
        
    except DataSchemaError as e:
        logger.critical(f"Data Schema Error: {e}")
        sys.exit(1)
    except ValueError as e:
        if "Target not learnable" in str(e):
            logger.critical(f"Target Error: {e}")
            sys.exit(1)
        logger.error(f"Value Error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error during T025b execution: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()