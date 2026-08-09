"""
Task T023a: Calculate Spearman correlation between VADER scores and manual scores.

This script aligns the VADER-derived cohesion proxy scores with the manually
annotated ground truth data and calculates the Spearman rank correlation coefficient (ρ).

It outputs a pass/fail result against the threshold ρ ≥ 0.5 (SC-005).

Dependencies:
- data/validation/manual_ground_truth.csv (ingested by T022b)
- data/derived/sentiment_scores.csv (output of sentiment analysis pipeline)
"""
import logging
import sys
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from config import get_config, ensure_directories_exist
from utils.logger import get_logger

# Constants
CORRELATION_THRESHOLD = 0.5
MIN_SAMPLES_FOR_VALIDATION = 5  # Minimum pairs required to calculate correlation

def load_and_align_data(logger: logging.Logger) -> Optional[pd.DataFrame]:
    """
    Load VADER scores and manual ground truth, then align them on common keys.
    
    Returns:
        DataFrame with aligned scores, or None if alignment fails.
    """
    config = get_config()
    
    # Define paths
    manual_ground_truth_path = config["paths"]["data_validation"] / "manual_ground_truth.csv"
    # Assuming sentiment analysis output is in derived data
    sentiment_scores_path = config["paths"]["data_derived"] / "sentiment_scores.csv"
    
    if not manual_ground_truth_path.exists():
        logger.error(f"Manual ground truth file not found: {manual_ground_truth_path}")
        logger.error("Task T022b (ingestion of ground truth) must be completed before T023a.")
        return None
    
    if not sentiment_scores_path.exists():
        logger.error(f"Sentiment scores file not found: {sentiment_scores_path}")
        logger.error("Sentiment analysis pipeline (T018-T021) must be completed before T023a.")
        return None
    
    logger.info(f"Loading manual ground truth from {manual_ground_truth_path}")
    manual_df = pd.read_csv(manual_ground_truth_path)
    
    logger.info(f"Loading sentiment scores from {sentiment_scores_path}")
    sentiment_df = pd.read_csv(sentiment_scores_path)
    
    # Validate required columns
    required_manual_cols = {"project_id", "comment_id", "manual_cohesion_score"}
    required_sentiment_cols = {"project_id", "comment_id", "vader_compound"}
    
    missing_manual = required_manual_cols - set(manual_df.columns)
    missing_sentiment = required_sentiment_cols - set(sentiment_df.columns)
    
    if missing_manual:
        logger.error(f"Missing columns in manual ground truth: {missing_manual}")
        return None
    if missing_sentiment:
        logger.error(f"Missing columns in sentiment scores: {missing_sentiment}")
        return None
    
    # Select and rename columns for merging
    manual_subset = manual_df[["project_id", "comment_id", "manual_cohesion_score"]].copy()
    sentiment_subset = sentiment_df[["project_id", "comment_id", "vader_compound"]].copy()
    
    # Merge on project_id and comment_id
    logger.info("Aligning datasets on project_id and comment_id...")
    aligned_df = pd.merge(
        manual_subset,
        sentiment_subset,
        on=["project_id", "comment_id"],
        how="inner"
    )
    
    if aligned_df.empty:
        logger.error("No matching records found between manual ground truth and sentiment scores.")
        logger.error("Check that comment_ids and project_ids match exactly.")
        return None
    
    logger.info(f"Aligned {len(aligned_df)} records for validation.")
    return aligned_df

def calculate_spearman_correlation(df: pd.DataFrame, logger: logging.Logger) -> Tuple[Optional[float], Optional[float], bool]:
    """
    Calculate Spearman rank correlation between manual_cohesion_score and vader_compound.
    
    Args:
        df: Aligned DataFrame with columns 'manual_cohesion_score' and 'vader_compound'.
        logger: Logger instance.
        
    Returns:
        Tuple of (correlation_coefficient, p_value, pass_status)
        Returns (None, None, False) if calculation is not possible.
    """
    if len(df) < MIN_SAMPLES_FOR_VALIDATION:
        logger.warning(f"Insufficient samples ({len(df)}) for reliable correlation calculation. "
                     f"Minimum required: {MIN_SAMPLES_FOR_VALIDATION}")
        return None, None, False
    
    # Drop any rows with NaN values
    clean_df = df.dropna(subset=["manual_cohesion_score", "vader_compound"])
    
    if len(clean_df) < MIN_SAMPLES_FOR_VALIDATION:
        logger.warning(f"Insufficient non-null samples ({len(clean_df)}) after cleaning.")
        return None, None, False
    
    try:
        rho, p_value = spearmanr(clean_df["manual_cohesion_score"], clean_df["vader_compound"])
        
        # Handle edge case where correlation might be NaN (e.g., constant values)
        if np.isnan(rho):
            logger.warning("Spearman correlation is NaN (possibly constant values in one or both variables).")
            return None, None, False
        
        pass_status = rho >= CORRELATION_THRESHOLD
        
        logger.info(f"Spearman correlation (ρ): {rho:.4f} (p-value: {p_value:.4f})")
        logger.info(f"Threshold: {CORRELATION_THRESHOLD}")
        logger.info(f"Result: {'PASS' if pass_status else 'FAIL'}")
        
        return rho, p_value, pass_status
        
    except Exception as e:
        logger.error(f"Error calculating Spearman correlation: {e}")
        return None, None, False

def run_validation_pipeline(logger: logging.Logger) -> bool:
    """
    Execute the full validation pipeline for T023a.
    
    Returns:
        True if the pipeline completed successfully (regardless of pass/fail result).
        False if the pipeline failed due to missing data or errors.
    """
    logger.info("Starting T023a: Spearman Correlation Validation")
    
    # Load and align data
    aligned_df = load_and_align_data(logger)
    if aligned_df is None:
        logger.error("Failed to load and align data. Validation cannot proceed.")
        return False
    
    # Calculate correlation
    rho, p_value, pass_status = calculate_spearman_correlation(aligned_df, logger)
    
    if rho is None:
        logger.error("Correlation calculation failed or was not possible.")
        return False
    
    # Log final result
    result_message = (
        f"T023a Validation Result: {'PASS' if pass_status else 'FAIL'}\n"
        f"Spearman ρ: {rho:.4f}\n"
        f"P-value: {p_value:.4f}\n"
        f"Threshold: {CORRELATION_THRESHOLD}\n"
        f"Sample size: {len(aligned_df)}"
    )
    
    logger.info("=" * 60)
    logger.info(result_message)
    logger.info("=" * 60)
    
    return True

def main():
    """Entry point for the validation script."""
    config = get_config()
    ensure_directories_exist(config)
    
    logger = get_logger(__name__)
    logger.info("T023a: Spearman Correlation Validation Script Started")
    
    success = run_validation_pipeline(logger)
    
    if success:
        logger.info("T023a completed successfully.")
        sys.exit(0)
    else:
        logger.error("T023a failed due to data or execution errors.")
        sys.exit(1)

if __name__ == "__main__":
    main()
